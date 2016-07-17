import mapnik
import math
import os
import time
import config

class Renderer:

	def __init__(self, id, config):
		self.id = id
		if not os.path.exists("tiles/%s" % (self.id)):
			os.makedirs("tiles/%s" % (self.id))

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
		symbolizer.fill = mapnik.Color("#ff9900")
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

		mapnik.render_to_file(m, "tiles/%s/%s_%s_%s.png" % (self.id, z, x, y), "png")

	def tiles(self, minzoom, maxzoom):
		for z in range(minzoom, maxzoom + 1):
			n = 2 ** z
			for x in range(0, n):
				for y in range(0, n):
					print "%s %s %s %s" % (self.id, z, x, y)
					self.tile(x, y, z)

renderer = Renderer(395457, config)
start_time = time.time()
renderer.tiles(1, 7)
print("--- %s seconds ---" % (time.time() - start_time))
