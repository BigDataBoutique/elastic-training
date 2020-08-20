from geomet import wkt
import json
from dictor import dictor

import pyarrow as pa
import pyarrow.parquet as pq
import s3fs
import pandas as pd

with open('paloalto.geojson', mode='rb') as f:
  d = json.load(f)

results = []

for i in d['features']:
  result = {}
  name = dictor(i,"properties.name:en")
  type = dictor(i,"geometry.type")
  geojson = dictor(i, "geometry")
  if type in ['Polygon','MultiPolygon']:
    result['name'] = name
    result['coordinates'] = wkt.dumps(geojson,decimals=7)
    results.append(result)
#
data_frame = pd.DataFrame(results)
table = pa.Table.from_pandas(data_frame)

filesystem = s3fs.S3FileSystem()
path = "s3://bdbq-israel-boundaries/pa"
pq.write_to_dataset(table, root_path=path, compression='gzip', filesystem=filesystem)
