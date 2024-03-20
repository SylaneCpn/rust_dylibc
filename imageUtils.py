#!/usr/bin/env python
# -*- coding: utf-8 -*-
#-----------------------------------------------------------------------------

import sys
import os
import platform
import ctypes
import traceback
import time

try:
  import Tkinter # python 2
except:
  import tkinter as Tkinter # python 3

class Record:
  __init__=lambda self, **kw: self.__dict__.update(**kw)
  __repr__=lambda self: repr(self.__dict__)
  __eq__=lambda self, oth: oth is not None and self.__dict__==oth.__dict__
  __getitem__=lambda self, attr: self.__dict__.__getitem__(attr)
  __setitem__=lambda self, attr, value: self.__dict__.__setitem__(attr, value)
  get=lambda self, attr, default=None: self.__dict__.get(attr, default)

class CB:
  def __init__(self, cb, *args, **kw):
    self.cb=cb
    self.args=args
    self.kw=kw
  #
  def __call__(self, *args, **kw):
    return self.cb(self, *args, **kw)

def makeFrame(app, fnct, img1, img2):
  app.fnct=fnct
  app.w1=img1[0]
  app.h1=img1[1]
  app.d1=img1[2]
  pfx=('P6\n%d %d\n255\n'%(app.w1, app.h1)).encode()
  offset=len(pfx)
  app.d=bytearray(offset+len(app.d1))
  for i in range(offset): app.d[i]=pfx[i]
  if img2:
    app.w2=img2[0]
    app.h2=img2[1]
    app.d2=img2[2]
    app.work=lambda a: a.fnct(a.w1, a.h1, a.d1,
                              a.w2, a.h2, a.d2, a.sclValue, a.d)
  else:
    app.w2=0
    app.h2=0
    app.d2=None
    app.work=lambda a: a.fnct(a.w1, a.h1, a.d1, a.sclValue, a.d)
  app.outFile='output_'+fnct.__name__+'.ppm'
  if not Tkinter._default_root: Tkinter.Tk().withdraw()
  app.top=Tkinter.Toplevel()
  app.top.title(app.outFile)
  app.top.wm_protocol('WM_DELETE_WINDOW', CB(quitCmd, app))
  app.top.rowconfigure(0, weight=1)
  app.top.rowconfigure(1, weight=0)
  app.top.columnconfigure(0, weight=1)
  app.photo=Tkinter.PhotoImage(width=app.w1, height=app.h1)
  app.ppmConvert=None
  app.ppm=None
  app.lbl=Tkinter.Label(app.top)
  app.lbl.config(width=app.w1, height=app.h1, anchor='nw', image=app.photo)
  app.lbl.grid(row=0, column=0, sticky='nsew')
  if fnct.__name__=='imgBlend':
    sclMax=100
    app.sclScroll=5
  else:
    sclMax=8
    app.sclScroll=1
  app.scl=Tkinter.Scale(app.top, orient=Tkinter.HORIZONTAL,
                        from_=0, to=sclMax, resolution=1,
                        command=CB(scaleCmd, app))
  app.scl.grid(row=1, column=0, sticky='nsew')
  app.top.minsize(2+app.w1, 4+app.h1+app.scl.winfo_reqheight())
  app.top.bind("<KeyPress-Escape>", CB(quitCmd, app))
  app.top.bind("<KeyPress-q>", CB(quitCmd, app))
  app.top.bind('<ButtonPress-4>', CB(mouseWheelCmd, app))
  app.top.bind('<ButtonPress-5>', CB(mouseWheelCmd, app))
  app.lastMouseWheel=0
  app.sclValue=-1
  app.times=None
  app.timeIdx=0
  app.scl.set(sclMax)
  if app.d2: app.scl.set(0)

def updatePpm(app):
  if app.ppmConvert is None:
    # depending on python/tkinter versions (and bugs), some conversions
    # are required when providing Tkinter.PhotoImage data
    # - python 3 wants bytes() and directly accesses them
    # - python 2 wants utf-8 encoded str() but decodes it to bytes again!
    app.ppmConvert=[] # one of these should work...
    if 0: # memory leak!!!
      app.ppmConvert.append(lambda ppm: app.top.tk._createbytearray(ppm))
    if Tkinter.__name__=='tkinter': # bad utf-8 conversions in python 2
      app.ppmConvert.append(lambda ppm: bytes(ppm))
    app.ppmConvert.append(lambda ppm: ppm.decode('latin-1').encode('utf-8'))
    app.ppmConvert.append(lambda ppm: ppm.decode('latin-1').encode('utf-8') \
                                         .replace(b'\x00', b'\xc0\x80'))
  while app.ppmConvert:
    try:
      ppm=app.ppmConvert[0](app.d)
      # FIXME: some versions of Tkinter.PhotoImage have a memory leak!
      #        (probably in tk._createbytearray)
      #        thus we perform a direct call to Tcl/Tk
      if 0:
        app.photo.config(width=app.w1, height=app.h1,
                         format='ppm', data=ppm)
      else:
        app.top.tk.call(app.photo.name, 'configure',
                        '-width', app.w1, '-height', app.h1,
                        '-format', 'ppm', '-data', ppm)
      break # this conversion was suitable
    except:
      # traceback.print_exc()
      del app.ppmConvert[0] # forget this conversion which was not suitable

def quitCmd(helper, *args, **kw):
  app=helper.args[0]
  sys.stdout.write('Saving `%s\'\n'%app.outFile)
  open(app.outFile, 'wb').write(app.d)
  Tkinter._default_root.quit()

def mouseWheelCmd(helper, evt, *args, **kw):
  app=helper.args[0]
  if evt.serial!=app.lastMouseWheel:
    app.lastMouseWheel=evt.serial
    if evt.num==4:
      app.scl.set(app.sclValue+app.sclScroll)
    elif evt.num==5:
      app.scl.set(app.sclValue-app.sclScroll)

def scaleCmd(helper, sclValue, *args, **kw):
  app=helper.args[0]
  sclValue=int(sclValue)
  if sclValue!=app.sclValue:
    app.sclValue=sclValue
    timeFnct=time.time
    workFnct=app.work
    t0=timeFnct(); workFnct(app); t1=timeFnct()
    if not app.times:
      app.times=[t1-t0]*64
      app.times=(ctypes.c_double*len(app.times))(*app.times)
    app.times[app.timeIdx]=t1-t0
    app.timeIdx=(app.timeIdx+1)%len(app.times)
    sys.stdout.write('average %s() time: %g\n'%
                     (app.fnct.__name__, sum(app.times)/len(app.times)))
    updatePpm(app)

def imgBlend(w1, h1, d1, w2, h2, d2, k, d):
  offset=len(d)-3*w1*h1
  ratio=k/100.0
  compRatio=1.0-ratio
  for y1 in range(h1):
    for x1 in range(w1):
      x2=int(x1*w2/w1)
      y2=int(y1*h2/h1)
      i1=x1+y1*w1
      i2=x2+y2*w2
      d[offset+3*i1+0]=int(d1[3*i1+0]*compRatio+d2[3*i2+0]*ratio)
      d[offset+3*i1+1]=int(d1[3*i1+1]*compRatio+d2[3*i2+1]*ratio)
      d[offset+3*i1+2]=int(d1[3*i1+2]*compRatio+d2[3*i2+2]*ratio)

def imgReveal(w1, h1, d1, k, d):
  offset=len(d)-3*w1*h1
  shift=8-k
  for i in range(w1*h1):
    d[offset+3*i+0]=(d1[3*i+0]<<shift)&0x00FF
    d[offset+3*i+1]=(d1[3*i+1]<<shift)&0x00FF
    d[offset+3*i+2]=(d1[3*i+2]<<shift)&0x00FF

def imgHide(w1, h1, d1, w2, h2, d2, k, d):
  offset=len(d)-3*w1*h1
  shift=8-k
  mask=(~0)<<k
  for y1 in range(h1):
    for x1 in range(w1):
      x2=int(x1*w2/w1)
      y2=int(y1*h2/h1)
      i1=x1+y1*w1
      i2=x2+y2*w2
      d[offset+3*i1+0]=((d1[3*i1+0]&mask)|(d2[3*i2+0]>>shift))&0x00FF
      d[offset+3*i1+1]=((d1[3*i1+1]&mask)|(d2[3*i2+1]>>shift))&0x00FF
      d[offset+3*i1+2]=((d1[3*i1+2]&mask)|(d2[3*i2+2]>>shift))&0x00FF

def loadPpm(fileName):
  try:
    input=open(fileName, 'rb')
    words=[]
    while len(words)<4:
      words+=input.readline().split(b'#')[0].split()
    if len(words)!=4 or words[0]!=b'P6' or words[3]!=b'255': return None
    (w,h)=(int(words[1]),int(words[2]))
    nb=3*w*h
    d=bytearray(input.read(nb))
    if len(d)!=nb: return None
    return (w, h, d)
  except:
    # traceback.print_exc()
    return None

def main():
  app=Record()
  if len(sys.argv)>1:
    fnct=sys.argv[1]
    if fnct in ['blend', 'reveal', 'hide']:
      fnct='img%s%s'%(fnct[0].upper(),fnct[1:])
      fnct=getattr(sys.modules[__name__], fnct)
      expectedArgs=3 if fnct.__name__=='imgReveal' else 4
      if len(sys.argv)==expectedArgs:
        img1=loadPpm(sys.argv[2])
        if not img1:
          sys.stderr.write('\nCannot open image `%s\'\n'%sys.argv[2])
          sys.exit(1)
        if expectedArgs==4:
          img2=loadPpm(sys.argv[3])
          if not img2:
            sys.stderr.write('\nCannot open image `%s\'\n'%sys.argv[3])
            sys.exit(1)
        else:
          img2=None
        makeFrame(app, fnct, img1, img2)
  if app.get('top') is not None:
    Tkinter._default_root.mainloop() 
  else:
    sys.stderr.write('\n')
    sys.stderr.write('usage: %s blend image1 image2\n'%sys.argv[0])
    sys.stderr.write('       %s reveal image\n'%sys.argv[0])
    sys.stderr.write('       %s hide image1 image2\n'%sys.argv[0])
    sys.stderr.write('\n')

def tryToLoadNativeFunctions():
  try:
    dirName=os.path.dirname(sys.modules[__name__].__file__)
    if not dirName: dirName=os.path.curdir
    libName='NativeImageUtils'
    if platform.system().startswith('Windows'):
      libName='./target/debug/%s.dll'%libName
    elif platform.system().startswith('Darwin'):
      libName='./target/debug/lib%s.dylib'%libName
    else:
      libName='./target/debug/lib%s.so'%libName
    path=os.path.join(dirName, libName)
    ntvLib=ctypes.CDLL(os.path.abspath(path))
    ntvHello=ntvLib['hello']
    ntvHello.restype=ctypes.c_int
    ntvHello.argtypes=[ctypes.c_char_p] # msg
    sys.stdout.write('native hello() returned: %d\n'%
                     ntvHello(b'native code is accessible!'))
    try:
      ntvImgBlend=ntvLib['imgBlend']
      ntvImgBlend.restype=None
      ntvImgBlend.argtypes=[ctypes.c_int,    # w1
                            ctypes.c_int,    # h1
                            ctypes.c_void_p, # d1
                            ctypes.c_int,    # w2
                            ctypes.c_int,    # h2
                            ctypes.c_void_p, # d2
                            ctypes.c_int,    # k
                            ctypes.c_void_p] # d
      def imgBlend(w1, h1, d1, w2, h2, d2, k, d):
        nb1=3*w1*h1
        nb2=3*w2*h2
        ntvImgBlend(w1, h1, (ctypes.c_uint8*nb1).from_buffer(d1),
                    w2, h2, (ctypes.c_uint8*nb2).from_buffer(d2),
                    k, (ctypes.c_uint8*nb1).from_buffer(d, len(d)-nb1))
      setattr(sys.modules[__name__], 'imgBlend', imgBlend)
      sys.stdout.write('native version of imgBlend() made available\n')
    except:
      #traceback.print_exc()
      pass
    try:
      ntvImgReveal=ntvLib['imgReveal']
      ntvImgReveal.restype=None
      ntvImgReveal.argtypes=[ctypes.c_int,    # w1
                             ctypes.c_int,    # h1
                             ctypes.c_void_p, # d1
                             ctypes.c_int,    # k
                             ctypes.c_void_p] # d
      def imgReveal(w1, h1, d1, k, d):
        nb1=3*w1*h1
        ntvImgReveal(w1, h1, (ctypes.c_uint8*nb1).from_buffer(d1),
                     k, (ctypes.c_uint8*nb1).from_buffer(d, len(d)-nb1))
      setattr(sys.modules[__name__], 'imgReveal', imgReveal)
      sys.stdout.write('native version of imgReveal() made available\n')
    except:
      #traceback.print_exc()
      pass
    try:
      ntvImgHide=ntvLib['imgHide']
      ntvImgHide.restype=None
      ntvImgHide.argtypes=[ctypes.c_int,    # w1
                           ctypes.c_int,    # h1
                           ctypes.c_void_p, # d1
                           ctypes.c_int,    # w2
                           ctypes.c_int,    # h2
                           ctypes.c_void_p, # d2
                           ctypes.c_int,    # k
                           ctypes.c_void_p] # d
      def imgHide(w1, h1, d1, w2, h2, d2, k, d):
        nb1=3*w1*h1
        nb2=3*w2*h2
        ntvImgHide(w1, h1, (ctypes.c_uint8*nb1).from_buffer(d1),
                   w2, h2, (ctypes.c_uint8*nb2).from_buffer(d2),
                   k, (ctypes.c_uint8*nb1).from_buffer(d, len(d)-nb1))
      setattr(sys.modules[__name__], 'imgHide', imgHide)
      sys.stdout.write('native version of imgHide() made available\n')
    except:
      #traceback.print_exc()
      pass
  except:
    #traceback.print_exc()
    pass

if __name__=='__main__':
  tryToLoadNativeFunctions()
  main()

#-----------------------------------------------------------------------------
