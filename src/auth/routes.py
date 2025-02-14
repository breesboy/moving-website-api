from fastapi import APIRouter,Depends,status
from .schemas import UserCreateModel, UserModel, UserLoginModel, CurrentUser, EmailModel, PasswordResetRequestModel, PasswordResetConfirmModel
from .services import UserService
from src.db.main import get_session
from sqlmodel.ext.asyncio.session import AsyncSession
from fastapi.exceptions import HTTPException
from typing import List
from .utils import create_access_token, decode_token, verify_password, create_url_safe_token, decode_url_safe_token,generate_passwd_hash
from datetime import timedelta,datetime
from fastapi.responses import JSONResponse
from .dependencies import RefreshTokenBearer,AccessTokenBearer, get_current_user,RoleChecker
from src.db.redis import add_jti_to_blocklist
from src.mail import mail, create_message
from src.config import Config


auth_router = APIRouter()
user_service = UserService()

user_role_checker = RoleChecker(['admin','user'])
admin_role_checker = RoleChecker(['admin'])

REFRESH_TOKEN_EXPIRY = 2


# @auth_router.post("/send-mail")
# async def send_mail(emails:EmailModel):
# 	emails = emails.addresses

# 	message = create_message(
#         recipients=emails,
#         subject="Verify Your Email",
#         template_name="email.html",
#         context={"name": "test", "verification_link": "google.com"},
#     )

# 	await mail.send_message(message, template_name="email.html")

# 	return {"message":"Email sent successfully"}




@auth_router.post('/signup', status_code=status.HTTP_201_CREATED)
async def create_user_Account(user_data:UserCreateModel, session: AsyncSession = Depends(get_session)):
	email = user_data.email
	username = user_data.username

	username_exists = await user_service.username_exists(username, session)

	if username_exists:
		raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Username already exists")
	
	email_exists = await user_service.email_exists(email, session)

	if email_exists:
		raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User email already exists")

	new_user = await user_service.create_user_Account(user_data,session)

	token = create_url_safe_token({"email": email})

	link = f"http://{Config.DOMAIN}/api/v1/auth/verify/{token}"

	message = create_message(
        recipients=[email],
        subject="Verify Your Email",
        template_name="verify-email.html",
        context={"name": username, "verification_link": link},
    )
	await mail.send_message(message, template_name="verify-email.html")

	return {
		"message": "User created successfully. Check your email to verify your account",
		"user": new_user
	}

@auth_router.get("/get_all_users", response_model=list[UserModel])
async def get_all_users(session:AsyncSession = Depends(get_session), _=Depends(AccessTokenBearer()),__:bool = Depends(admin_role_checker)):
	users = await user_service.get_all_users(session)

	return users

@auth_router.get("/verify/{token}")
async def verify_email(token:str, session: AsyncSession = Depends(get_session)):
	token_data = decode_url_safe_token(token)
	user_email = token_data.get("email")

	if user_email:
		user = await user_service.get_user_by_email(user_email,session)

		if not user:
			raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
		
		await user_service.update_user(user, {"is_verified": True}, session)


		return JSONResponse(content={
			"message":"Email verified successfully"},
			status_code=status.HTTP_200_OK
			)
	return JSONResponse(content={
		"message":"Error occured while verifying email"},
		status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
		)


@auth_router.post("/login")
async def login_user(login_data:UserLoginModel, session: AsyncSession = Depends(get_session)):
	email = login_data.email
	password = login_data.password

	user = await user_service.get_user_by_email(email, session)

	if user is not None:
		password_valid = verify_password(password, user.password_hash)

		if password_valid:
			access_token = create_access_token(
				user_data={
					"first_name": user.first_name,
					"last_name": user.last_name,
					"is_verified": user.is_verified,
					"user_uid": str(user.uid),
					"username": user.username,
					"email": user.email,
					"role": user.role

				}
			)

			refresh_token = create_access_token(
				user_data={
					"user_uid": str(user.uid),
					"username": user.username,
					"email": user.email
				},
				refresh=True,
				expiry=timedelta(days=REFRESH_TOKEN_EXPIRY)
			)

			return JSONResponse(
				content={
					"message": "Login successful",
					"access_token": access_token,
					"refresh_token": refresh_token,
					"user":{
						"user_uid": str(user.uid),
						"fist_name": user.first_name,
						"last_name": user.last_name,
						"is_verified": user.is_verified,
						"username": user.username,
						"email": user.email,
						"role": user.role

					}
				}
			)
		
	raise HTTPException(
		status_code=status.HTTP_403_FORBIDDEN,
		detail="Invalid email or password"
	)

@auth_router.post("/logout")
async def revoke_token(token_details: dict = Depends(AccessTokenBearer())):
	jti = token_details['jti']

	await add_jti_to_blocklist(jti)

	return JSONResponse(
		content={
			"message": "Loggout successfully"
		},
		status_code=status.HTTP_200_OK
	)


@auth_router.get("/refresh_token")
async def get_new_access_token(token_details: dict = Depends(RefreshTokenBearer())):
	expiry_timestamp = token_details['exp']

	if datetime.fromtimestamp(expiry_timestamp) > datetime.now():
		new_access_token = create_access_token(
			user_data=token_details['user']
		)

		return JSONResponse(
			content={
				"access_token": new_access_token
			}
		)
	
	raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired token")


@auth_router.get("/me", response_model=CurrentUser)
async def get_current_user(
    user=Depends(get_current_user), _:bool = Depends(user_role_checker)
):
    return user

@auth_router.post("/password-reset-request")
async def password_reset_request(email:PasswordResetRequestModel):
	email = email.email
	token = create_url_safe_token({"email": email})

	link = f"http://{Config.DOMAIN}/api/v1/auth/password-reset-confirm/{token}"

	message = create_message(
        recipients=[email],
        subject="Reset Your Password",
        template_name="reset-password.html",
        context={"name": email, "verification_link": link},
    )
	await mail.send_message(message, template_name="reset-password.html")

	return JSONResponse(content={
		"message": "Password reset link sent successfully"
		}, status_code=status.HTTP_200_OK)

@auth_router.post("/password-reset-confirm/{token}")
async def password_reset_confirm(token:str, password:PasswordResetConfirmModel, session: AsyncSession = Depends(get_session)):
	token_data = decode_url_safe_token(token)

	new_password = password.new_password
	password_hash = generate_passwd_hash(new_password)

	user_email = token_data.get("email")

	if user_email:
		user = await user_service.get_user_by_email(user_email,session)

		if not user:
			raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
		
		await user_service.update_user(user, {"password_hash": password_hash}, session)


		return JSONResponse(content={
			"message":"Password reset successfully"},
			status_code=status.HTTP_200_OK
			)
	return JSONResponse(content={
		"message":"Error occured during password reset"},
		status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
		)
