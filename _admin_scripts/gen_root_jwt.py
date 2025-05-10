import jwt, time, uuid
import dotenv
import os

dotenv.load_dotenv('../')
SECRET_KEY = os.getenv("JWT_SECRET", override=True)

payload = {
  "sub":"root",
  "role":"root",
  "iat":int(time.time()),
  "exp":int(time.time())+60*60*24*365*50,  # 50 yr
  "jti":uuid.uuid4().hex
}
print(jwt.encode(payload, "SECRET_KEY", algorithm="HS256"))