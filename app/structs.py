import struct

audio_packet_header = struct.Struct("<HH")  # ushort ID, ushort seq_number
