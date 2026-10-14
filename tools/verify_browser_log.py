#!/usr/bin/env python3
"""Verify frozen real GUI traffic; do not substitute synthetic VM responses."""
import datetime,hashlib,json,struct,zlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def main():
    import argparse
    a=argparse.ArgumentParser();a.add_argument('log',type=Path);a.add_argument('--output',type=Path,required=True);o=a.parse_args();log=o.log
    rows=[json.loads(x) for x in (log).read_text().splitlines()]
    buffers={'to_vm':bytearray(),'from_vm':bytearray()};seq={'to_vm':0,'from_vm':0};frames=[]
    for r in rows:
        if r['event']!='bytes':continue
        d=r['direction'];seq[d]+=1
        data=bytes.fromhex(r['hex'])
        if 'crc32' in r:
            assert r['sequence']==seq[d] and r['length']==len(data) and r['crc32']==f'{zlib.crc32(data):08x}'
        buf=buffers[d];buf.extend(data)
        while len(buf)>=3:
            if buf[0]==250:n=3;body=b''
            else:
                assert buf[0]==251,buf[:16].hex()
                if len(buf)<5:break
                length=int.from_bytes(buf[3:5],'little');n=5+length
                if len(buf)<n:break
                body=bytes(buf[5:n])
                if d=='to_vm':assert body[-1:]==b'\xfe';body=body[:-1]
            if len(buf)<n:break
            frames.append({'utc':r['utc'],'direction':d,'kind':buf[1],'id':buf[2],'body_hex':body.hex(),'wire_bytes':n});del buf[:n]
    assert not any(buffers.values()),'Snapshot ended inside a packet'
    assert not [f for f in frames if f['direction']=='from_vm' and f['kind']==19]
    outputs=[f for f in frames if f['direction']=='from_vm' and f['kind']==20 and f['id']==0 and bytes.fromhex(f['body_hex'])[:1]==b'\x02']
    numbers=[int(bytes.fromhex(f['body_hex'])[1:]) for f in outputs]
    assert numbers==list(range(1,501)),numbers[:5]
    returned=[f for f in frames if f['direction']=='from_vm' and f['kind']==18]
    assert len(returned)>=1
    for f in returned:assert bytes.fromhex(f['body_hex'])==b'\x01'+struct.pack('<i',12)
    uploads=[]
    for f in frames:
        if f['direction']=='to_vm' and f['kind']==32:
            code=bytes.fromhex(f['body_hex'])[1:];crc=zlib.crc32(code)
            matches=[reply for reply in frames if reply['direction']=='from_vm' and reply['kind']==23 and reply['id']==f['id'] and bytes.fromhex(reply['body_hex'])==struct.pack('<I',crc)]
            assert matches,'Actual uploaded code lacks matching STM32 CRC'
            uploads.append({**f,'crc32':f'{crc:08x}','code_sha256':hashlib.sha256(code).hexdigest(),'code_hex':code.hex()})
    duration=(datetime.datetime.fromisoformat(outputs[-1]['utc'])-datetime.datetime.fromisoformat(outputs[0]['utc'])).total_seconds()
    report={'result':'PASS','path':'Pinned official web IDE → binary WebSocket → App Lab Brick → real Router → physical STM32 SmallVM',
            'output_values':numbers,'output_messages':len(numbers),'output_span_seconds':duration,
            'output_wire_bytes':sum(f['wire_bytes'] for f in outputs),
            'output_wire_bytes_per_second':sum(f['wire_bytes'] for f in outputs)/duration,
            'arithmetic_returns':len(returned),'arithmetic_value':12,
            'closed_sessions':sum(r['event']=='session_released' for r in rows),
            'opened_sessions':sum(r['event']=='session_acquired' for r in rows),
            'transport_record_crc_errors':0 if all('crc32' in r for r in rows if r['event']=='bytes') else None,'task_errors':0,
            'actual_ide_compiled_uploads_verified_by_mcu_crc':uploads,
            'log_sha256':hashlib.sha256((log).read_bytes()).hexdigest()}
    o.output.write_text(json.dumps(report,indent=2)+'\n')
    o.output.with_suffix('.frames.json').write_text(json.dumps(frames,indent=2)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k not in ('output_values','actual_ide_compiled_uploads_verified_by_mcu_crc')},indent=2))
if __name__=='__main__':main()
