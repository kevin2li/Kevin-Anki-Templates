import re

s = """
{{c1::image-occlusion:rect:left=.6369:top=.4542:width=.1801:height=.0876:oi=1}}<br>{{c4::image-occlusion:rect:left=.6161:top=.7782:width=.1607:height=.0717:oi=1}}<br>{{c2::image-occlusion:rect:left=.4375:top=.6295:width=.1548:height=.0876:oi=1}}<br>{{c3::image-occlusion:rect:left=.436:top=.7782:width=.1637:height=.077:oi=1}}<br>{{c5::image-occlusion:rect:left=.041:top=.2629:width=.1269:height=.0746:oi=1}}<br>{{c6::image-occlusion:rect:left=.0366:top=.4494:width=.1493:height=.0719:oi=1}}<br>
"""

def occlusions2mask_groups(occlusions: str):
    pattern = r"\{\{c(\d+)::image-occlusion:rect:left=([\d.]+):top=([\d.]+):width=([\d.]+):height=([\d.]+):oi=1\}\}"
    result = {}
    for item in re.finditer(pattern, occlusions):
        k, left, top, width, height = item.groups()
        if k not in result:
            result[k] = []
        result[k] += [float(left), float(top), float(width), float(height)]
    mask_groups = [result[k] for k in result]
    return mask_groups

s = "<img src='aaa.png' />"
s = ""
res = occlusions2mask_groups(s)
print(res)