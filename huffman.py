"""
Nén và giải nén file văn bản bằng thuật toán Huffman.

Chương trình làm việc trên từng KÝ TỰ Unicode (đọc file với mã hóa UTF-8),
nên văn bản tiếng Việt có dấu được xử lý bình thường.

Cấu trúc file nén (.huf):
    [4 byte]  độ dài phần header (số nguyên không dấu, big-endian)
    [header]  chuỗi JSON (UTF-8): {"padding": p, "freq": {ký tự: tần suất}}
    [data]    chuỗi bit đã mã hóa, gom thành từng byte
"""

import heapq
import json


class Node:
    """Một nút của cây Huffman."""

    def __init__(self, freq, char=None, left=None, right=None):
        self.freq = freq      # tần suất (với nút trong: tổng tần suất 2 con)
        self.char = char      # ký tự (chỉ nút lá mới có)
        self.left = left      # con trái  -> bit 0
        self.right = right    # con phải  -> bit 1

    def is_leaf(self):
        return self.left is None and self.right is None


# ---------------------------------------------------------------------------
# Bước 2: Đếm tần suất xuất hiện của từng ký tự - O(n)
# ---------------------------------------------------------------------------
def count_frequency(text):
    freq = {}
    for ch in text:
        freq[ch] = freq.get(ch, 0) + 1
    return freq


# ---------------------------------------------------------------------------
# Bước 3: Xây dựng cây Huffman bằng Min Heap - O(k log k)
# ---------------------------------------------------------------------------
def build_tree(freq):
    if not freq:
        return None

    # Mỗi phần tử trong heap là bộ (tần suất, thứ tự, nút).
    # "thứ tự" dùng để phân xử khi hai nút có cùng tần suất. Nhờ duyệt ký tự
    # theo thứ tự sắp xếp, lúc nén và lúc giải nén luôn dựng ra cùng một cây.
    heap = []
    order = 0
    for ch in sorted(freq):
        heap.append((freq[ch], order, Node(freq[ch], ch)))
        order += 1
    heapq.heapify(heap)

    # Lặp k - 1 lần: lấy 2 nút có tần suất nhỏ nhất, gộp thành 1 nút cha.
    while len(heap) > 1:
        f1, _, left = heapq.heappop(heap)
        f2, _, right = heapq.heappop(heap)
        parent = Node(f1 + f2, left=left, right=right)
        heapq.heappush(heap, (parent.freq, order, parent))
        order += 1

    return heap[0][2]  # nút còn lại duy nhất là gốc của cây


# ---------------------------------------------------------------------------
# Bước 4: Tạo bảng mã Huffman bằng cách duyệt cây
# ---------------------------------------------------------------------------
def build_codes(root):
    codes = {}
    if root is None:
        return codes

    # Trường hợp đặc biệt: văn bản chỉ có 1 loại ký tự -> cây chỉ có 1 nút.
    # Gán mã "0" để mỗi ký tự vẫn chiếm 1 bit.
    if root.is_leaf():
        codes[root.char] = "0"
        return codes

    def traverse(node, code):
        if node.is_leaf():
            codes[node.char] = code
            return
        traverse(node.left, code + "0")   # đi sang trái: thêm bit 0
        traverse(node.right, code + "1")  # đi sang phải: thêm bit 1

    traverse(root, "")
    return codes


# ---------------------------------------------------------------------------
# Bước 5: Mã hóa văn bản thành chuỗi bit và gom bit thành byte
# ---------------------------------------------------------------------------
def encode(text, codes):
    return "".join(codes[ch] for ch in text)


def bits_to_bytes(bits):
    # Thêm các bit 0 vào cuối để độ dài chia hết cho 8 (padding).
    padding = (8 - len(bits) % 8) % 8
    bits += "0" * padding

    data = bytearray()
    for i in range(0, len(bits), 8):
        data.append(int(bits[i:i + 8], 2))  # 8 bit -> 1 byte
    return bytes(data), padding


def compress_file(input_path, output_path):
    """Nén file văn bản.

    Trả về (text, freq, codes, số bit sau mã hóa, số byte của header).
    """
    # Bước 1: đọc file văn bản. newline="" để giữ nguyên ký tự xuống dòng.
    with open(input_path, "r", encoding="utf-8", newline="") as f:
        text = f.read()

    freq = count_frequency(text)
    root = build_tree(freq)
    codes = build_codes(root)
    bits = encode(text, codes)
    data, padding = bits_to_bytes(bits)

    # Header lưu bảng tần suất để lúc giải nén dựng lại đúng cây Huffman.
    # separators=(",", ":") bỏ dấu cách thừa để header gọn hơn.
    header = json.dumps({"padding": padding, "freq": freq},
                        ensure_ascii=False, separators=(",", ":"))
    header = header.encode("utf-8")

    with open(output_path, "wb") as f:
        f.write(len(header).to_bytes(4, "big"))
        f.write(header)
        f.write(data)

    return text, freq, codes, len(bits), 4 + len(header)


# ---------------------------------------------------------------------------
# Bước 6: Giải nén và khôi phục dữ liệu ban đầu
# ---------------------------------------------------------------------------
def bytes_to_bits(data, padding):
    bits = "".join(format(byte, "08b") for byte in data)  # 1 byte -> 8 bit
    if padding > 0:
        bits = bits[:-padding]  # bỏ các bit 0 đã thêm lúc nén
    return bits


def decode(bits, root):
    # Trường hợp chỉ có 1 loại ký tự: mỗi bit ứng với 1 ký tự.
    if root.is_leaf():
        return root.char * len(bits)

    result = []
    node = root
    for bit in bits:
        # Đi từ gốc xuống: bit 0 sang trái, bit 1 sang phải.
        node = node.left if bit == "0" else node.right
        if node.is_leaf():
            # Gặp lá: đã đọc xong mã của 1 ký tự, quay lại gốc.
            result.append(node.char)
            node = root
    return "".join(result)


def decompress_file(input_path, output_path):
    """Giải nén file .huf và ghi lại văn bản gốc. Trả về văn bản đã khôi phục."""
    with open(input_path, "rb") as f:
        header_len = int.from_bytes(f.read(4), "big")
        header = json.loads(f.read(header_len).decode("utf-8"))
        data = f.read()

    root = build_tree(header["freq"])  # dựng lại đúng cây đã dùng khi nén
    if root is None:
        text = ""  # file gốc rỗng
    else:
        bits = bytes_to_bits(data, header["padding"])
        text = decode(bits, root)

    with open(output_path, "w", encoding="utf-8", newline="") as f:
        f.write(text)
    return text
