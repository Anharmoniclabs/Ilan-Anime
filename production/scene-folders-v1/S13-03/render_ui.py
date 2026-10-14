from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).parent
FONT = '/usr/share/fonts/inter/InterVariable.ttf'
def font(n): return ImageFont.truetype(FONT, n)
messages = [
    "that 'is this anything' email",
    'JC',
    'where are you',
    "ok i'm not waiting. it's not spam. it's so much worse than spam",
    "you in a hole. you're in a hole aren't you",
    "i can see your location you absolute bobo. don't move.",
]
denise = 'Hi JC! Quick heads up, the board is holding your milestone payment until our partner review next week. Just process!'
def lines(draw, text, width, face):
    result=[]; line=''
    for word in text.split():
        trial=(line+' '+word).strip()
        if draw.textlength(trial,font=face)>width and line: result.append(line);line=word
        else: line=trial
    if line: result.append(line)
    return result
def render(end=False):
    im=Image.new('RGB',(1280,720),'#14202b'); d=ImageDraw.Draw(im)
    x=420; width=440
    d.rounded_rectangle((x-10,8,x+width+10,712),radius=32,fill='#080d12',outline='#697079',width=2)
    d.rounded_rectangle((x,20,x+width,700),radius=26,fill='#ede9e0')
    d.text((x+22,31),'2:15',font=font(16),fill='#172331')
    d.text((x+22,65),'Sofía',font=font(26),fill='#14202b')
    d.line((x+16,106,x+width-16,106),fill='#c3c4c3',width=2)
    y=120
    for text in messages if end else messages[:1]:
        ls=lines(d,text,width-64,font(19));h=len(ls)*24+18
        d.rounded_rectangle((x+16,y,x+width-32,y+h),radius=12,fill='#d6dce0')
        for line in ls:d.text((x+28,y+8),line,font=font(19),fill='#172331');y+=24
        y+=28
    if end:
        ls=lines(d,denise,width-64,font(18));h=len(ls)*23+48
        top=min(y+2,680-h)
        d.rounded_rectangle((x+10,top,x+width-10,top+h),radius=14,fill='#142f49',outline='#cdb37d',width=1)
        d.text((x+24,top+9),'Denise',font=font(19),fill='#f2d398')
        yy=top+36
        for line in ls:d.text((x+24,yy),line,font=font(18),fill='#faf7ed');yy+=23
    d.rounded_rectangle((x+150,688,x+290,692),radius=2,fill='#263440')
    target=ROOT/('end' if end else 'start')/('end-local-ui.png' if end else 'start-local-ui.png')
    target.parent.mkdir(exist_ok=True);im.save(target)
if __name__=='__main__':
    render(False);render(True)
