import onetimepass as otp
my_secret = 'IXQ6TQ37ZCSM7NXODJFFUXQOBY'
my_token = otp.get_hotp_token(my_secret,5)

print my_token