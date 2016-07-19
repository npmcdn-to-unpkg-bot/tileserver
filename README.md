# tileserver

This is a simple tile server that serves OBIS species distribution tiles. Tiles are prerendered using [Mapnik](http://mapnik.org/) and stored in [MongoDB](https://www.mongodb.com). Blank tiles are not stored.

Points are rendered in red but layers are given different colors using a hue rotate filter on the [Leaflet](http://leafletjs.com/) client.