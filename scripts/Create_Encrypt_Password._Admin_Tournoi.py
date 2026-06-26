"""
Code qui genere password du login admin de l'application Tournoi
variable  ADMIN_PASS_HASH
pwd = b"!!0007" pour railway
pwd = b"1" pour le dev (question de rapidité)
"""

import bcrypt

pwd = b"!!0007"
hashed = bcrypt.hashpw(pwd, bcrypt.gensalt())
print(hashed.decode())