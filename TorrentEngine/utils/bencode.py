class BenCodeError(Exception):
    pass

def _decode_bytes(data:bytes) -> tuple[bytes,bytes]:
    """
    This one will decode bytes
    """
    try:
        col_idx = data.index(b':')
    except ValueError:
        raise BenCodeError("Invalid Byte String: Missing Colon Delim")
    try:
        length = int(data[:col_idx])
    except ValueError:
        raise BenCodeError("Invalid Byte String Length")
    start = col_idx+1
    end = start+length
    if end > len(data):
        raise BenCodeError("Invalid byte string: Length Prefix Out Of Bound")
    return data[start:end], data[end:]

def _decode_integer(data:bytes) -> tuple[int,bytes]:
    """
    for the decoding of integer
    """
    try:
        end_idx = data.index(b'e')
    except ValueError:
        raise BenCodeError("Invalid integer, missing trailing 'e' delim")
    try:
        val = int(data[1:end_idx])
    except ValueError:
        raise BenCodeError("Invalid Integer Value Parsing")
    return val,data[end_idx+1:]

def _decode_next(data:bytes) -> tuple[any,bytes]:
    if not data:
        raise BenCodeError("Empty stream")
    prefix = data[0:1]
    if prefix == b'i':
        return _decode_integer(data)
    elif prefix == b'l':
        return _decode_list(data)
    elif prefix == b'd':
        return _decode_dict(data)
    elif prefix.isdigit():
        return _decode_bytes(data)
    else:
        raise BenCodeError(f"Unexpected token prefix: {prefix}")

def _decode_dict(data:bytes) -> tuple[dict,bytes]:
    rest = data[1:] 
    dictionary = {}
    while rest and rest[0:1] != b'e':
        if not rest[0:1].isdigit():
            raise BenCodeError("Invalid dictionary")
        raw_key, rest = _decode_bytes(rest)
        key = raw_key.decode('utf-8') 
        val, rest = _decode_next(rest)
        dictionary[key] = val 
    if not rest:
        raise BenCodeError("Invalid dictionary")
    return dictionary, rest[1:]

def _decode_list(data:bytes) -> tuple[list,bytes]:
    """parses a bencoded list"""
    rest = data[1:]
    lst = []
    while rest and rest[0:1] != b'e':
        val, rest = _decode_next(rest)
        lst.append(val)
    if not rest:
        raise BenCodeError("Invalid list: Missing trailing 'e' delimiter.")
    return lst,rest[1:]

def bdecode(data: bytes) -> any:
    try:
        result, rest = _decode_next(data)
        if rest:
            raise BenCodeError("Data found after main bencode structure ended.")
        return result
    except Exception as e:
        if not isinstance(e, BenCodeError):
            raise BenCodeError(f"Bencode parsing failed: {str(e)}")
        raise e

def bencode(item: any) -> bytes:
    """
    lexicogrpahical order
    """
    if isinstance(item, int):
        return f"i{item}e".encode('utf-8') 
    elif isinstance(item, bytes):
        return f"{len(item)}:".encode('utf-8') + item   
    elif isinstance(item, str):
        encoded_str = item.encode('utf-8')
        return f"{len(encoded_str)}:".encode('utf-8') + encoded_str  
    elif isinstance(item, list):
        payload = b"".join(bencode(element) for element in item)
        return b"l" + payload + b"e"  
    elif isinstance(item, dict):
        # keys sorted lexicographically by binary key value.
        sorted_keys = sorted(item.keys())
        payload = b""
        for key in sorted_keys:
            encoded_key = bencode(key)
            encoded_value = bencode(item[key])
            payload += encoded_key + encoded_value
        return b"d" + payload + b"e" 
    raise TypeError(f"Unsupported type for bencoding: {type(item)}")