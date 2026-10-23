//! Strict canonical RFC4648 alphabet/padding; no whitespace or extra output allocation above limit.
use super::PinnedRegistryError as E;
pub(super) fn decode(s:&str,maximum:usize)->Result<Vec<u8>,E>{
    let b=s.as_bytes();if b.is_empty()||b.len()%4!=0{return Err(E::Encoding);}
    let padding=usize::from(b.last()==Some(&b'='))+usize::from(b.get(b.len()-2)==Some(&b'='));
    let length=(b.len()/4).checked_mul(3).and_then(|n|n.checked_sub(padding)).filter(|n|*n<=maximum).ok_or(E::Limit)?;
    let mut out=Vec::new();out.try_reserve_exact(length).map_err(|_|E::Limit)?;
    for(n,c)in b.chunks_exact(4).enumerate(){
        let a=value(c[0])?;let v=value(c[1])?;let last=(n+1)*4==b.len();
        if c[2]==b'='{
            if !last||c[3]!=b'='||v&15!=0{return Err(E::Encoding);}out.push((a<<2)|(v>>4));
        }else{
            let x=value(c[2])?;out.push((a<<2)|(v>>4));out.push((v<<4)|(x>>2));
            if c[3]==b'=' {if !last||x&3!=0{return Err(E::Encoding);}}
            else{out.push((x<<6)|value(c[3])?);}
        }
    }
    if out.len()!=length{return Err(E::Encoding);}Ok(out)
}
fn value(b:u8)->Result<u8,E>{match b{b'A'..=b'Z'=>Ok(b-b'A'),b'a'..=b'z'=>Ok(b-b'a'+26),b'0'..=b'9'=>Ok(b-b'0'+52),b'+'=>Ok(62),b'/'=>Ok(63),_=>Err(E::Encoding)}}
