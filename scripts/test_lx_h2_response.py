#!/usr/bin/env python3
"""Run the real Swift H2 receive loop against bytes from a local TLS/H2 fixture.
Networking adapter is Python ssl/h2; this is NOT the iOS TLSClient integration.
"""
import os, shutil, socket, ssl, subprocess, tempfile, threading
from pathlib import Path
from h2.config import H2Configuration
from h2.connection import H2Connection
ROOT=Path(__file__).resolve().parents[1]
def declaration(text, marker):
    start=text.index(marker); end=text.index('{',start)+1; depth=1
    while depth:
        if text[end]=='{': depth+=1
        elif text[end]=='}': depth-=1
        end+=1
    return text[start:end]
with tempfile.TemporaryDirectory(prefix='lx-h2-',dir=os.environ.get('TMPDIR')) as tmp:
    tmp=Path(tmp)
    subprocess.run(['openssl','req','-x509','-newkey','rsa:2048','-nodes','-subj','/CN=localhost','-days','1','-keyout',str(tmp/'key'),'-out',str(tmp/'cert')],check=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    server=socket.socket(); server.bind(('127.0.0.1',0)); server.listen(1)
    context=ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER); context.load_cert_chain(tmp/'cert',tmp/'key'); context.set_alpn_protocols(['h2'])
    errors=[]
    status=os.environ.get('LX_FIXTURE_STATUS','403')
    def serve():
        try:
            with context.wrap_socket(server.accept()[0],server_side=True) as stream:
                assert stream.selected_alpn_protocol()=='h2'
                h=H2Connection(config=H2Configuration(client_side=False)); h.initiate_connection(); stream.sendall(h.data_to_send())
                while True:
                    events=h.receive_data(stream.recv(65535))
                    if any(type(e).__name__=='RequestReceived' for e in events):
                        # Deliberately hold END_STREAM open: a rejection must fail now,
                        # not wait for EOF or an unrelated proxy timeout.
                        h.send_headers(1,[(':status',status),('content-type','text/event-stream')],end_stream=False)
                        if status=='200': h.send_data(1,b'pong',end_stream=True)
                        stream.sendall(h.data_to_send()); break
        except Exception as e: errors.append(e)
    thread=threading.Thread(target=serve); thread.start()
    ctx=ssl.create_default_context(cafile=str(tmp/'cert')); ctx.set_alpn_protocols(['h2'])
    client=H2Connection(); client.initiate_connection()
    with ctx.wrap_socket(socket.create_connection(server.getsockname()),server_hostname='localhost') as stream:
        assert stream.selected_alpn_protocol()=='h2'
        client.send_headers(1,[(':method','GET'),(':scheme','https'),(':authority','localhost'),(':path','/down/session')],end_stream=True)
        stream.sendall(client.data_to_send()); captured=b''
        while True:
            data=stream.recv(65535); captured+=data
            if any(type(e).__name__=='ResponseReceived' for e in client.receive_data(data)): break
    thread.join(); server.close()
    if errors: raise errors[0]
    # Feed actual server frames, then a sentinel EOF. Before the fix the 403 is
    # swallowed and receiveH2Data reads the sentinel instead of rejecting.
    frames=[]; offset=0
    while offset+9<=len(captured):
        n=int.from_bytes(captured[offset:offset+3],'big'); frames.append((captured[offset+3],captured[offset+4],int.from_bytes(captured[offset+5:offset+9],'big'),captured[offset+9:offset+9+n])); offset+=9+n
    source='''import Foundation
import Synchronization
struct FixtureEOF: Error {}
enum Phase { case live, halfClosed }
struct State {
 var h2DataBuffer=Data(); var phase=Phase.live; var h2ResponseReceived=false
 var h2ConnectionReceiveConsumed=0; var h2StreamReceiveConsumed=0; var h2LocalWindowSize=4194304
 var h2PeerConnectionWindow=65535; var h2PacketStreamWindows: [UInt32:Int]=[:]; var h2PeerStreamSendWindow=65535
 var h2FlowGate=Gate()
}
struct Gate { func wakeAll() {} }
struct Frame { var type:UInt8; var flags:UInt8; var streamId:UInt32; var payload:Data }
struct H2Framing { typealias Frame = FixtureFrame; static func readUInt32(_ d:Data)->UInt32 { d.reduce(0){($0<<8)|UInt32($1)} } }
typealias FixtureFrame=Frame
actor Reader { var frames:[Frame]; init(_ f:[Frame]) { frames=f }; func readFrame() throws -> Frame { if frames.isEmpty {throw FixtureEOF()}; return frames.removeFirst() } }
struct Wire { func send(_ d:Data) async throws {} }
enum AnywhereError: Error { enum ProtocolKind {case xhttp}; enum Reason {case streamClosed; case handshakeFailed(detail:String)}; case proxy(ProtocolKind,Reason) }
final class XHTTPConnection: Sendable {
 let state=Mutex(State()); let h2FrameReader:Reader; let download=Wire(); let h2DownloadStreamId:UInt32=1
 init(_ f:[Frame]) {h2FrameReader=Reader(f)}
 func markH2Closed() {state.withLock{$0.phase = .halfClosed}}
 func parseH2Settings(_ d:Data) {}
 func buildH2Frame(type:UInt8,flags:UInt8,streamId:UInt32,payload:Data)->Data {Data()}
'''
    h2=(ROOT/'Shared/Networking/Protocols/VLESS/XHTTP/XHTTPConnection+H2.swift').read_text()
    transport=(ROOT/'Shared/Networking/Protocols/VLESS/XHTTP/XHTTPConnection+H2Transport.swift').read_text()
    for line in h2.splitlines():
        if 'static let h2' in line: source+=line+'\n'
    source+=declaration(h2,'    func checkH2ResponseStatus(')+'\n'+declaration(h2,'    private static func huffmanDecodeDigits(')+'\n'
    source+=declaration(transport,'    func receiveH2Data(')+'\n}\n'
    swiftframes=','.join(f'Frame(type:{t},flags:{f},streamId:{s},payload:Data([{",".join(map(str,p))}]))' for t,f,s,p in frames)
    source+='''
let semaphore=DispatchSemaphore(value:0)
Task.detached {
 do { _ = try await XHTTPConnection(['''+swiftframes+''']).receiveH2Data(); print("FAIL: rejected response accepted"); exit(1) }
 catch AnywhereError.proxy(.xhttp,.handshakeFailed(let detail)) { print("PASS: live TLS/H2 403 rejected immediately: \\(detail)"); semaphore.signal() }
 catch { print("FAIL: 403 swallowed; read continued to \\(error)"); exit(1) }
}
semaphore.wait()
'''
    if status=='200':
        source=source.replace('do { _ = try await XHTTPConnection(', 'do { let received = try await XHTTPConnection(')
        source=source.replace('print("FAIL: rejected response accepted"); exit(1)', 'if received != Data("pong".utf8) { print("FAIL: payload mismatch"); exit(1) }; print("PASS: live TLS/H2 200 data delivered"); semaphore.signal()')
    script=tmp/'main.swift'; script.write_text(source)
    env=os.environ.copy()
    if env.get('SWIFT_LIBRARY_PATH'): env['LD_LIBRARY_PATH']=env['SWIFT_LIBRARY_PATH']
    frontend=shutil.which(env.get('SWIFT_FRONTEND','swift-frontend'))
    if frontend is None:
        raise RuntimeError('Swift frontend not found on PATH')
    obj=tmp/'main.o'; binary=tmp/'test'
    subprocess.run([frontend,'-c','-O','-swift-version','6',str(script),'-o',str(obj)],env=env,check=True)
    swiftlib=str(Path(frontend).resolve().parents[1]/'lib/swift/linux')
    extra=[]
    if env.get('SWIFT_LIBRARY_PATH'):
        runtime=env['SWIFT_LIBRARY_PATH'].split(':')
        extra=['-L'+runtime[0],'-L'+runtime[1],str(Path(runtime[0])/'ld-linux-x86-64.so.2'),str(Path(runtime[0])/'libc.so.6'),str(Path(runtime[0])/'libm.so.6'),str(Path(runtime[1])/'libstdc++.so.6'),'-Wl,-rpath-link,'+runtime[0],'-Wl,-rpath-link,'+runtime[1]]
    subprocess.run(['gcc']+extra+[str(obj),'-o',str(binary),'-L'+swiftlib,'-Wl,-rpath,'+swiftlib,'-lswiftCore','-lswift_Concurrency','-lFoundation','-lFoundationEssentials','-ldispatch','-lswiftDispatch','-lswiftSynchronization','-lm','-lpthread','-ldl']+extra,check=True)
    if env.get('SWIFT_LIBRARY_PATH'):
        loader=str(Path(env['SWIFT_LIBRARY_PATH'].split(':')[0])/'ld-linux-x86-64.so.2')
        cmd=[loader,'--library-path',env['SWIFT_LIBRARY_PATH']+':'+swiftlib,str(binary)]
    else: cmd=[str(binary)]
    raise SystemExit(subprocess.run(cmd,timeout=30).returncode)
