import os
from pathlib import Path
from datetime import datetime, timedelta, timezone

from dotenv import load_dotenv
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from passlib.context import CryptContext

load_dotenv(Path(__file__).with_name(".env"))

SECRET_KEY = os.getenv("SECRET_KEY", "change-this-secret-key")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "1440"))

password_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
bearer_scheme = HTTPBearer(auto_error=False)


def hash_password(password: str) -> str:
	return password_context.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
	return password_context.verify(password, password_hash)


def create_access_token(data: dict) -> str:
	payload = data.copy()
	payload["exp"] = datetime.now(timezone.utc) + timedelta(
		minutes=ACCESS_TOKEN_EXPIRE_MINUTES
	)
	return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def _decode_token(credentials: HTTPAuthorizationCredentials | None) -> dict:
	if not credentials or credentials.scheme.lower() != "bearer":
		raise HTTPException(
			status_code=status.HTTP_401_UNAUTHORIZED,
			detail="Authentication required",
			headers={"WWW-Authenticate": "Bearer"},
		)

	try:
		payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
	except JWTError as exc:
		raise HTTPException(
			status_code=status.HTTP_401_UNAUTHORIZED,
			detail="Invalid or expired token",
			headers={"WWW-Authenticate": "Bearer"},
		) from exc

	if not payload.get("sub") or not payload.get("role"):
		raise HTTPException(
			status_code=status.HTTP_401_UNAUTHORIZED,
			detail="Invalid token payload",
			headers={"WWW-Authenticate": "Bearer"},
		)
	return payload


def get_current_patient(
	credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> dict:
	payload = _decode_token(credentials)
	if payload.get("role") != "patient":
		raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Patient access required")
	return {"patient_id": payload["sub"], "full_name": payload.get("name", "")}


def get_current_admin(
	credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> dict:
	payload = _decode_token(credentials)
	if payload.get("role") != "admin":
		raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")
	return {"admin_id": payload["sub"], "full_name": payload.get("name", "")}
