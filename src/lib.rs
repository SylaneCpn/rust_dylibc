use std::os::raw::*;

#[repr(C)]
#[derive(Debug)]
pub struct Pixel {
    pub r: u8,
    pub g: u8,
    pub b: u8,
}



#[no_mangle]
pub extern "C" fn hello(msg :*const c_char)-> c_int {
    let message = unsafe { std::ffi::CStr::from_ptr(msg) }.to_string_lossy();
    println!("native hello() received '{}' and is about to return {}",
    message, message.len());
    message.len() as c_int
}

#[no_mangle]
pub extern "C" fn imgBlend(
         w1 : c_int,          // first input image (and result) width
         h1 : c_int,          // first input image (and result) height
         d1 : *const Pixel, // first input image pixels (w1*h1)
         w2 : c_int,          // second input image width
         h2 : c_int,          // second input image height
         d2 : *const Pixel, // second input image pixels (w2*h2)
         k : c_int,           // cursor value within range [0;100]
         d: *mut Pixel)        // resulting image pixels (w1*h1)
{
    
let coeff : f64 = k as f64 /100.0;
let mcoeff : f64 = 1.0 - coeff;

let arr1 = unsafe {std::slice::from_raw_parts(d1,(w1*h1) as usize)};
let arr2 = unsafe {std::slice::from_raw_parts(d2,(w2*h2) as usize)};
let mut res_arr = unsafe {std::slice::from_raw_parts_mut(d,(w1*h1) as usize)};

for y1 in 0..h1 {
  for x1 in 0..w1 {

    let x2 : c_int = x1 *w2/w1;
    let y2 : c_int =y1  *h2/h1;

    let i1 : usize =(x1 +y1*w1) as usize;
    let i2 : usize =(x2 +y2*w2) as usize;
  
    res_arr[i1].r = (arr2[i2].r as f64 * coeff + arr1[i1].r as f64 * mcoeff) as u8;
    res_arr[i1].g = (arr2[i2].g as f64 * coeff + arr1[i1].g as f64 * mcoeff) as u8;
    res_arr[i1].b = (arr2[i2].b as f64 * coeff + arr1[i1].b as f64 * mcoeff) as u8;
  }
}
    
 
}

#[no_mangle]
pub extern "C" fn imgReveal(
         w1 : c_int,          // first input image (and result) width
         h1 : c_int,          // first input image (and result) height
         d1 : *const Pixel, // first input image pixels (w1*h1)
         k : c_int,           // cursor value within range [0;100]
         d: *mut Pixel)        // resulting image pixels (w1*h1)
{
    let shift = 8 - k;
    let arr1 = unsafe {std::slice::from_raw_parts(d1,(w1*h1) as usize)};
    let mut res_arr = unsafe {std::slice::from_raw_parts_mut(d,(w1*h1) as usize)};

    let range : usize = (w1*h1) as usize; 

    for i in 0..range {
    res_arr[i].r = if shift < 8 {arr1[i].r << shift} else {0};
    res_arr[i].g = if shift < 8 {arr1[i].g << shift} else {0};
    res_arr[i].b = if shift < 8 {arr1[i].b << shift} else {0};
    }

}


#[no_mangle]
pub extern "C" fn imgHide(
         w1 : c_int,          // first input image (and result) width
         h1 : c_int,          // first input image (and result) height
         d1 : *const Pixel, // first input image pixels (w1*h1)
         w2 : c_int,          // second input image width
         h2 : c_int,          // second input image height
         d2 : *const Pixel, // second input image pixels (w2*h2)
         k : c_int,           // cursor value within range [0;100]
         d: *mut Pixel)        // resulting image pixels (w1*h1)
{
  
    
    
    let arr1 = unsafe {std::slice::from_raw_parts(d1,(w1*h1) as usize)};
    let arr2 = unsafe {std::slice::from_raw_parts(d2,(w2*h2) as usize)};
    let mut res_arr = unsafe {std::slice::from_raw_parts_mut(d,(w1*h1) as usize)};
    
    let mask = if k < 8 { 0xFF << k} else {0};
    let shift = 8 - k; 

    for y1 in 0..h1 {
      for x1 in 0..w1 {
    
        let x2 : c_int = x1 *w2/w1;
        let y2 : c_int =y1  *h2/h1;
    
        let i1 : usize =(x1 +y1*w1) as usize;
        let i2 : usize =(x2 +y2*w2) as usize;
      
        res_arr[i1].r =  if shift < 8 {arr2[i2].r >> shift | (arr1[i1].r & mask)} else {arr1[i1].r};
        res_arr[i1].g = if shift < 8 {arr2[i2].g >> shift | (arr1[i1].g & mask)} else {arr1[i1].g};
        res_arr[i1].b = if shift < 8 {arr2[i2].b >> shift | (arr1[i1].b & mask)} else {arr1[i1].b};
      }
    }
        
     
}
