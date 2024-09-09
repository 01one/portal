import os.path
from tornado.web import RequestHandler, Application, StaticFileHandler
from tornado.ioloop import IOLoop
import socketio
import secrets
from http.cookies import SimpleCookie

#Use Environment variable to store the app password instead of of source code

PASSWORD = "12345"

def check_password(user_password):
	return user_password == PASSWORD

class LoginHandler(RequestHandler):
	async def get(self):
		await self.render('login.html')

class IndexHandler(RequestHandler):
	async def get(self):
		if not self.get_secure_cookie('authenticated'):
			self.redirect('/')
			return
		await self.render('index.html')

class AuthenticateHandler(RequestHandler):
	async def post(self):
		user_password = self.get_body_argument('password')
		if check_password(user_password):
			self.set_secure_cookie('authenticated', 'true')
			self.redirect('/index')
		else:
			self.set_status(401)
			self.write("Authentication failed")

sio = socketio.AsyncServer(async_mode='tornado')

@sio.event
async def connect(sid, environ):
	cookie_header = environ.get('HTTP_COOKIE', '')
	cookie = SimpleCookie(cookie_header)
	
	auth_cookie = cookie.get('authenticated')
	print(auth_cookie)
	if not auth_cookie:
		print(f"Client {sid} failed authentication.")
		await sio.disconnect(sid)
	else:
		print(f"Client {sid} connected successfully.")

@sio.event
async def disconnect(sid):
	print('Client disconnected:', sid)

@sio.event
async def text_update(sid, data):
	await sio.emit('text_update', data, skip_sid=sid)

@sio.event
async def file_upload(sid, data):
	await sio.emit('file_download', data, skip_sid=sid)

if __name__ == "__main__":

	# Generate a random cookie_secret
	cookie_secret = secrets.token_hex(16)

	settings = {
		'cookie_secret': cookie_secret,
		'login_url': '/login',
		'debug': True
	}

	app = Application([
		(r'/', LoginHandler),
		(r'/index', IndexHandler),
		(r'/authenticate', AuthenticateHandler),
		(r'/static/(.*)', StaticFileHandler, {'path': os.path.join(os.getcwd(), 'static')}),
		(r"/socket.io/", socketio.get_tornado_handler(sio)),
	], **settings)
	
	port=9000

	app.listen(port)
	print(f"Server is running on http://localhost:{port}")
	IOLoop.current().start()
