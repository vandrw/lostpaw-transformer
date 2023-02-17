from glob import glob
import sys
from PIL import Image, ImageDraw


images = [Image.open(f) for a in sys.argv[1:] for f in glob(a)]

print("nr of images:", len(images))

padding = 5

result = Image.new('RGB', (sum(i.width + padding for i in images) - padding, max(i.height for i in images)))
result_draw = ImageDraw.Draw(result)
result_draw.rectangle((0, 0, result.width, result.height), "white")
x_offset = 0
for im in images:
  result.paste(im, (x_offset,0))
  x_offset += im.width + padding

result.save('result.png')
