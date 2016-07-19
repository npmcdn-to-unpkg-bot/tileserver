import mapnik
import math
import os
import time
import config
import pymongo
import StringIO
import PIL.Image
from io import BytesIO
from bson.binary import Binary

class Renderer:

	def __init__(self, id, config):
		self.id = id
		client = pymongo.MongoClient()
		self.db = client.tiles
		self.db.tiles.ensure_index([
			("id", pymongo.ASCENDING),
			("xyz", pymongo.ASCENDING)
		])
		if not os.path.exists("tiles/%s" % (self.id)):
			os.makedirs("tiles/%s" % (self.id))

		buf = BytesIO()
		im = PIL.Image.new("RGBA", (256, 256))
		im.save(buf, "png")
		self.blanksize = buf.__sizeof__()
		print "Blank size: %i" % (self.blanksize)
		self.db.blank.drop()
		self.db.blank.insert_one({ "tile": Binary(buf.getvalue()) })

		self.datasource = mapnik.PostGIS(
			host = config.host,
			user = config.user,
			password = config.password,
			dbname = "obis",
			table = "(select geom from explore.points where species_id = %s) points" % (self.id),
			geometry_field = "geom",
			srid = "4326",
			extent = "%s, %s, %s, %s" % (-180, -90, 180, 90),
			connext_timeout = 10
		)

		self.style = mapnik.Style()
		rule = mapnik.Rule()
		symbolizer = mapnik.MarkersSymbolizer()
		symbolizer.width = 5.0
		symbolizer.stroke_width = 0.0
		symbolizer.fill = mapnik.Color("#ffffff")
		symbolizer.opacity = 1.0
		symbolizer.allow_overlap = mapnik.Expression("True")
		rule.symbols.append(symbolizer)
		self.style.rules.append(rule)

	def deg(self, x, y, z):
		n = 2.0 ** z
		lon_deg = x / n * 360.0 - 180.0
		lat_rad = math.atan(math.sinh(math.pi * (1 - 2 * y / n)))
		lat_deg = math.degrees(lat_rad)
		return (lon_deg, lat_deg)

	def tile(self, x, y, z):
		nw = self.deg(x, y, z)
		se = self.deg(x + 1, y + 1, z)
		xmin = nw[0]
		ymin = se[1]
		xmax = se[0]
		ymax = nw[1]

		m = mapnik.Map(256, 256)
		m.srs = "+proj=merc +lon_0=0 +k=1 +x_0=0 +y_0=0 +a=6378137 +b=6378137 +towgs84=0,0,0,0,0,0,0 +units=m +no_defs"

		m.append_style("pointstyle", self.style)
		layer = mapnik.Layer("pointlayer")
		layer.datasource = self.datasource
		layer.styles.append("pointstyle")
		m.layers.append(layer)

		bbox = mapnik.Box2d(xmin, ymin, xmax, ymax)
		merc = mapnik.Projection(m.srs)
		longlat = mapnik.Projection("+proj=longlat +ellps=WGS84 +datum=WGS84 +no_defs")
		transform = mapnik.ProjTransform(longlat, merc)
		merc_bbox = transform.forward(bbox)

		m.zoom_to_box(merc_bbox)
		m.buffer_size = 10

		im = mapnik.Image(256, 256)
		mapnik.render(m, im)
		ims = im.tostring()
		pim = PIL.Image.frombuffer("RGBA", (256, 256), ims, "raw", "RGBA", 0, 1)
		buf = BytesIO()
		pim.save(buf, "png")
		self.db.tiles.remove({
			"id": self.id,
			"xyz": "%s_%s_%s" % (x, y, z)
		})
		if buf.__sizeof__() == self.blanksize:
			self.db.tiles.insert_one({
				"id": self.id,
				"xyz": "%s_%s_%s" % (x, y, z),
				"blank": True
			})
		else:
			self.db.tiles.insert_one({
				"id": self.id,
				"xyz": "%s_%s_%s" % (x, y, z),
				"tile": Binary(buf.getvalue())
			})

	def tiles(self, minzoom, maxzoom):
		for z in range(minzoom, maxzoom + 1):
			n = 2 ** z
			for x in range(0, n):
				for y in range(0, n):
					print "%s %s %s %s" % (self.id, z, x, y)
					self.tile(x, y, z)

start_time = time.time()
Renderer(395450, config).tiles(1, 8)
Renderer(395457, config).tiles(1, 8)
print("--- %s seconds ---" % (time.time() - start_time))
