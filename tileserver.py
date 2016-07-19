import BaseHTTPServer
import config
import pymongo

class Handler(BaseHTTPServer.BaseHTTPRequestHandler):

	def __init__(self, request, client_address, server):
		client = pymongo.MongoClient()
		self.db = client.tiles
		self.blank = self.db.blank.find_one({})
		BaseHTTPServer.BaseHTTPRequestHandler.__init__(self, request, client_address, server)

	def do_GET(self):
		print self.path
		params = self.path.split("/")

		if len(params) == 3:
			query = {
				"id": int(params[1]),
				"xyz": params[2]
			}
			tile = self.db.tiles.find_one(query)
			if "blank" in tile and tile["blank"]:
				self.send_response(200)
				self.send_header("Content-type", "image/png")
				self.end_headers()
				self.wfile.write(self.blank["tile"])
			else:
				self.send_response(200)
				self.send_header("Content-type", "image/png")
				self.end_headers()
				self.wfile.write(tile["tile"])

if __name__ == '__main__':
	server_class = BaseHTTPServer.HTTPServer
	httpd = server_class(("localhost", 8080), Handler)
	try:
		httpd.serve_forever()
	except KeyboardInterrupt:
		pass
	httpd.server_close()