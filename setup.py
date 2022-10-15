import pathlib
import os
from subprocess import check_call

def generate_proto_code():
    proto_interface_dir = "./protos/"
    generated_src_dir = "./generated/"
    out_folder = "."
    if not os.path.exists(generated_src_dir):
        os.mkdir(generated_src_dir)
    proto_it = pathlib.Path().glob(proto_interface_dir + "/**/*")
    proto_path = "generated=" + proto_interface_dir
    protos = [str(proto) for proto in proto_it if proto.is_file()]
    check_call(["protoc"] + protos + ["--python_out", out_folder, "--proto_path", proto_path])


if __name__=='__main__':
    generate_proto_code()