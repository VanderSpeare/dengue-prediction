import pandas as pd
import numpy as np
import re
import logging
from datetime import datetime
from pathlib import Path

try:
    from . import paths
    from .mongo_data_service import mongo_data_service
except ImportError:
    import paths
    try:
        from mongo_data_service import mongo_data_service
    except ImportError:
        mongo_data_service = None

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

# Mapping from 63 old provinces (and their variants) to 34 new province names
MERGE_MAP = {
    'tuyên quang': 'Tuyên Quang', 'hà giang': 'Tuyên Quang',
    'lào cai': 'Lào Cai', 'yên bái': 'Lào Cai',
    'thái nguyên': 'Thái Nguyên', 'bắc kạn': 'Thái Nguyên',
    'hải phòng': 'Hải Phòng', 'hải dương': 'Hải Phòng',
    'hồ chí minh': 'TP. Hồ Chí Minh', 'bà rịa - vũng tàu': 'TP. Hồ Chí Minh', 'bình dương': 'TP. Hồ Chí Minh',
    'phú thọ': 'Phú Thọ', 'vĩnh phúc': 'Phú Thọ', 'hòa bình': 'Phú Thọ',
    'bắc ninh': 'Bắc Ninh', 'bắc giang': 'Bắc Ninh',
    'hưng yên': 'Hưng Yên', 'thái bình': 'Hưng Yên',
    'ninh bình': 'Ninh Bình', 'hà nam': 'Ninh Bình', 'nam định': 'Ninh Bình',
    'quảng trị': 'Quảng Trị', 'quảng bình': 'Quảng Trị',
    'đà nẵng': 'Đà Nẵng', 'quảng nam': 'Đà Nẵng',
    'quảng ngãi': 'Quảng Ngãi', 'kon tum': 'Quảng Ngãi',
    'gia lai': 'Gia Lai', 'bình định': 'Gia Lai',
    'khánh hòa': 'Khánh Hòa', 'ninh thuận': 'Khánh Hòa',
    'lâm đồng': 'Lâm Đồng', 'đắk nông': 'Lâm Đồng', 'bình thuận': 'Lâm Đồng',
    'đắk lắk': 'Đắk Lắk', 'phú yên': 'Đắk Lắk',
    'đồng nai': 'Đồng Nai', 'bình phước': 'Đồng Nai',
    'tây ninh': 'Tây Ninh', 'long an': 'Tây Ninh',
    'cần thơ': 'Cần Thơ', 'sóc trăng': 'Cần Thơ', 'hậu giang': 'Cần Thơ',
    'vĩnh long': 'Vĩnh Long', 'bến tre': 'Vĩnh Long', 'trà vinh': 'Vĩnh Long',
    'đồng tháp': 'Đồng Tháp', 'tiền giang': 'Đồng Tháp',
    'cà mau': 'Cà Mau', 'bạc liêu': 'Cà Mau',
    'an giang': 'An Giang', 'kiên giang': 'An Giang',
    'hà nội': 'Hà Nội', 'huế': 'Huế', 'thừa thiên huế': 'Huế',
    'lai châu': 'Lai Châu', 'điện biên': 'Điện Biên', 'sơn la': 'Sơn La',
    'lạng sơn': 'Lạng Sơn', 'quảng ninh': 'Quảng Ninh', 'thanh hóa': 'Thanh Hóa',
    'nghệ an': 'Nghệ An', 'hà tĩnh': 'Hà Tĩnh', 'cao bằng': 'Cao Bằng'
}

REQUIRED_COLUMNS = {'NgayVao', 'Diachi'}

# ---------------------------------------------------------------------------
# TỌA ĐỘ 34 TỈNH / THÀNH PHỐ
# ---------------------------------------------------------------------------
VN_PROVINCE_COORDS = {
    'TP. Hồ Chí Minh': {'lat': 10.7769, 'lon': 106.7009},
    'Hà Nội': {'lat': 21.0285, 'lon': 105.8542},
    'Đà Nẵng': {'lat': 16.0544, 'lon': 108.2022},
    'Hải Phòng': {'lat': 20.8449, 'lon': 106.6881},
    'Cần Thơ': {'lat': 10.0452, 'lon': 105.7469},
    'Huế': {'lat': 16.4637, 'lon': 107.5909},
    'Gia Lai': {'lat': 13.9833, 'lon': 108.0000},
    'Đắk Lắk': {'lat': 12.6667, 'lon': 108.0500},
    'Lâm Đồng': {'lat': 11.9404, 'lon': 108.4583},
    'Khánh Hòa': {'lat': 12.2388, 'lon': 109.1967},
    'Đồng Nai': {'lat': 10.9574, 'lon': 106.8427},
    'Tây Ninh': {'lat': 11.3100, 'lon': 106.0983},
    'Vĩnh Long': {'lat': 10.2537, 'lon': 105.9722},
    'Đồng Tháp': {'lat': 10.4578, 'lon': 105.6331},
    'An Giang': {'lat': 10.5216, 'lon': 105.1259},
    'Cà Mau': {'lat': 9.1769, 'lon': 105.1524},
    'Quảng Ngãi': {'lat': 15.1205, 'lon': 108.7923},
    'Quảng Trị': {'lat': 16.8167, 'lon': 107.1000},
    'Thanh Hóa': {'lat': 19.8075, 'lon': 105.7764},
    'Nghệ An': {'lat': 19.3333, 'lon': 104.8333},
    'Hà Tĩnh': {'lat': 18.3560, 'lon': 105.9058},
    'Ninh Bình': {'lat': 20.2539, 'lon': 105.9750},
    'Hưng Yên': {'lat': 20.6464, 'lon': 106.0511},
    'Bắc Ninh': {'lat': 21.1861, 'lon': 106.0763},
    'Phú Thọ': {'lat': 21.3989, 'lon': 105.2280},
    'Thái Nguyên': {'lat': 21.5942, 'lon': 105.8482},
    'Lạng Sơn': {'lat': 21.8537, 'lon': 106.7624},
    'Cao Bằng': {'lat': 22.6667, 'lon': 106.2500},
    'Tuyên Quang': {'lat': 21.8233, 'lon': 105.2181},
    'Lào Cai': {'lat': 22.4856, 'lon': 103.9707},
    'Sơn La': {'lat': 21.3283, 'lon': 103.9148},
    'Điện Biên': {'lat': 21.3869, 'lon': 103.0230},
    'Lai Châu': {'lat': 22.3964, 'lon': 103.4684},
    'Quảng Ninh': {'lat': 21.0069, 'lon': 107.2925}
}

# ---------------------------------------------------------------------------
# TỌA ĐỘ 24 QUẬN / HUYỆN TP. HỒ CHÍ MINH
# ---------------------------------------------------------------------------
HCMC_DISTRICT_COORDS = {
    'Quận 1': {'lat': 10.7756, 'lon': 106.7004},
    'Quận 3': {'lat': 10.7844, 'lon': 106.6844},
    'Quận 4': {'lat': 10.7578, 'lon': 106.7012},
    'Quận 5': {'lat': 10.7540, 'lon': 106.6634},
    'Quận 6': {'lat': 10.7481, 'lon': 106.6353},
    'Quận 7': {'lat': 10.7340, 'lon': 106.7308},
    'Quận 8': {'lat': 10.7242, 'lon': 106.6286},
    'Quận 10': {'lat': 10.7719, 'lon': 106.6678},
    'Quận 11': {'lat': 10.7628, 'lon': 106.6504},
    'Quận 12': {'lat': 10.8671, 'lon': 106.6412},
    'Bình Thạnh': {'lat': 10.8106, 'lon': 106.7091},
    'Gò Vấp': {'lat': 10.8387, 'lon': 106.6652},
    'Tân Bình': {'lat': 10.8014, 'lon': 106.6527},
    'Tân Phú': {'lat': 10.7901, 'lon': 106.6282},
    'Bình Tân': {'lat': 10.7656, 'lon': 106.6022},
    'Phú Nhuận': {'lat': 10.7992, 'lon': 106.6803},
    'Thủ Đức': {'lat': 10.8494, 'lon': 106.7537},
    'Thành Phố Thủ Đức': {'lat': 10.8494, 'lon': 106.7537},
    'Hóc Môn': {'lat': 10.8856, 'lon': 106.5947},
    'Củ Chi': {'lat': 11.0067, 'lon': 106.5134},
    'Nhà Bè': {'lat': 10.6583, 'lon': 106.7417},
    'Bình Chánh': {'lat': 10.6875, 'lon': 106.5750},
    'Cần Giờ': {'lat': 10.5106, 'lon': 106.8778}
}

# ---------------------------------------------------------------------------
# MAPPING PHƯỜNG / XÃ -> QUẬN / HUYỆN (TP.HCM)
# ---------------------------------------------------------------------------
HCMC_WARD_TO_DISTRICT = {
    'an phú đông': 'Quận 12',
    'thới an': 'Quận 12',
    'tân chánh hiệp': 'Quận 12',
    'hiệp thành': 'Quận 12',
    'tân thới nhất': 'Quận 12',
    'tân thới nhứt': 'Quận 12',
    'thạnh lộc': 'Quận 12',
    'thạnh xuân': 'Quận 12',
    'trung mỹ tây': 'Quận 12',
    'tân thới hiệp': 'Quận 12',
    'an phú': 'Thủ Đức',
    'an khánh': 'Thủ Đức',
    'cát lái': 'Thủ Đức',
    'hiệp bình': 'Thủ Đức',
    'hiệp bình chánh': 'Thủ Đức',
    'hiệp bình phước': 'Thủ Đức',
    'linh trung': 'Thủ Đức',
    'linh chiểu': 'Thủ Đức',
    'linh tây': 'Thủ Đức',
    'linh đông': 'Thủ Đức',
    'tam bình': 'Thủ Đức',
    'tam phú': 'Thủ Đức',
    'bình chiểu': 'Thủ Đức',
    'phước long': 'Thủ Đức',
    'phước long a': 'Thủ Đức',
    'phước long b': 'Thủ Đức',
    'phước bình': 'Thủ Đức',
    'long bình': 'Thủ Đức',
    'long trường': 'Thủ Đức',
    'long thạnh mỹ': 'Thủ Đức',
    'long phước': 'Thủ Đức',
    'tăng nhơn phú': 'Thủ Đức',
    'tăng nhơn phú a': 'Thủ Đức',
    'tăng nhơn phú b': 'Thủ Đức',
    'thảo điền': 'Thủ Đức',
    'thạnh mỹ lợi': 'Thủ Đức',
    'bình trưng': 'Thủ Đức',
    'bình trưng tây': 'Thủ Đức',
    'bình trưng đông': 'Thủ Đức',
    'bình quới': 'Bình Thạnh',
    'bình thạnh': 'Bình Thạnh',
    'bình lợi trung': 'Bình Thạnh',
    'thạnh mỹ tây': 'Bình Thạnh',
    'thanh đa': 'Bình Thạnh',
    'hàng xanh': 'Bình Thạnh',
    'gia định': 'Bình Thạnh',
    'cầu kiệu': 'Phú Nhuận',
    'đức nhuận': 'Phú Nhuận',
    'hạnh thông': 'Gò Vấp',
    'thông tây hội': 'Gò Vấp',
    'an nhơn': 'Gò Vấp',
    'an hội': 'Gò Vấp',
    'an hội đông': 'Gò Vấp',
    'an hội tây': 'Gò Vấp',
    'gò vấp': 'Gò Vấp',
    'bến thành': 'Quận 1',
    'cầu ông lãnh': 'Quận 1',
    'nhiêu lộc': 'Quận 3',
    'bàn cờ': 'Quận 3',
    'hòa hưng': 'Quận 10',
    'diên hồng': 'Quận 10',
    'chợ quán': 'Quận 5',
    'bình tiên': 'Quận 6',
    'minh phụng': 'Quận 6',
    'phú định': 'Quận 8',
    'chánh hưng': 'Quận 8',
    'khánh hội': 'Quận 4',
    'an lạc': 'Bình Tân',
    'bình hưng hòa': 'Bình Tân',
    'bình trị đông': 'Bình Tân',
    'tân tạo': 'Bình Tân',
    'phú thạnh': 'Tân Phú',
    'tây thạnh': 'Tân Phú',
    'tân sơn nhì': 'Tân Phú',
    'phú hòa': 'Tân Bình',
    'phú thọ hòa': 'Tân Phú',
    'tân bình': 'Tân Bình',
    'phú nhuận': 'Phú Nhuận',
    'đông thạnh': 'Hóc Môn',
    'bà điểm': 'Hóc Môn',
    'xuân thới thượng': 'Hóc Môn',
    'tân hiệp': 'Hóc Môn',
    'tân xuân': 'Hóc Môn',
    'nhị bình': 'Hóc Môn',
    'thới tam thôn': 'Hóc Môn',
    'tân thới nhì': 'Hóc Môn',
    'xuân thới đông': 'Hóc Môn',
    'trung chánh': 'Hóc Môn',
    'hóc môn': 'Hóc Môn',
    'củ chi': 'Củ Chi',
    'nhà bè': 'Nhà Bè',
    'bình chánh': 'Bình Chánh',
    'cần giờ': 'Cần Giờ'
}

# ---------------------------------------------------------------------------
# TỌA ĐỘ CHI TIẾT CẤP PHƯỜNG / XÃ (TP.HCM & CÁC TỈNH)
# ---------------------------------------------------------------------------
WARD_COORDS = {
    # Bình Thạnh
    'Phường Bình Lợi Trung': {'lat': 10.8228, 'lon': 106.7025},
    'Phường Thạnh Mỹ Tây': {'lat': 10.8035, 'lon': 106.7118},
    'Phường Bình Quới': {'lat': 10.8315, 'lon': 106.7350},
    'Phường Gia Định': {'lat': 10.8010, 'lon': 106.6955},
    'Phường 27': {'lat': 10.8320, 'lon': 106.7310},
    'Phường 25': {'lat': 10.8040, 'lon': 106.7150},
    'Phường 7': {'lat': 10.8030, 'lon': 106.6920},
    'Phường 15': {'lat': 10.7960, 'lon': 106.7080},
    'Phường 24': {'lat': 10.8070, 'lon': 106.7070},
    # Gò Vấp
    'Phường Hạnh Thông': {'lat': 10.8360, 'lon': 106.6660},
    'Phường Thông Tây Hội': {'lat': 10.8410, 'lon': 106.6620},
    'Phường An Nhơn': {'lat': 10.8480, 'lon': 106.6780},
    'Phường An Hội': {'lat': 10.8450, 'lon': 106.6580},
    'Phường An Hội Đông': {'lat': 10.8465, 'lon': 106.6610},
    'Phường An Hội Tây': {'lat': 10.8435, 'lon': 106.6540},
    'Phường 11': {'lat': 10.8390, 'lon': 106.6580},
    'Phường 16': {'lat': 10.8470, 'lon': 106.6690},
    # Quận 12
    'Phường An Phú Đông': {'lat': 10.8520, 'lon': 106.6970},
    'Phường Thới An': {'lat': 10.8710, 'lon': 106.6540},
    'Phường Tân Chánh Hiệp': {'lat': 10.8620, 'lon': 106.6190},
    'Phường Hiệp Thành': {'lat': 10.8770, 'lon': 106.6340},
    'Phường Thạnh Lộc': {'lat': 10.8730, 'lon': 106.6850},
    'Phường Thạnh Xuân': {'lat': 10.8840, 'lon': 106.6760},
    'Phường Tân Thới Hiệp': {'lat': 10.8580, 'lon': 106.6380},
    # Thủ Đức
    'Phường Hiệp Bình': {'lat': 10.8410, 'lon': 106.7260},
    'Phường Hiệp Bình Chánh': {'lat': 10.8350, 'lon': 106.7210},
    'Phường Hiệp Bình Phước': {'lat': 10.8510, 'lon': 106.7190},
    'Phường An Khánh': {'lat': 10.7850, 'lon': 106.7320},
    'Phường Cát Lái': {'lat': 10.7710, 'lon': 106.7860},
    'Phường Phước Long': {'lat': 10.8280, 'lon': 106.7720},
    'Phường Long Bình': {'lat': 10.8760, 'lon': 106.8400},
    'Phường Long Trường': {'lat': 10.8030, 'lon': 106.8220},
    'Phường Bình Trưng': {'lat': 10.7890, 'lon': 106.7640},
    # Phú Nhuận
    'Phường Cầu Kiệu': {'lat': 10.7930, 'lon': 106.6850},
    'Phường Đức Nhuận': {'lat': 10.8020, 'lon': 106.6790},
    'Phường 10': {'lat': 10.7970, 'lon': 106.6760},
    # Quận 1 & 3 & 4 & 5 & 6 & 8 & 10
    'Phường Bến Thành': {'lat': 10.7720, 'lon': 106.6980},
    'Phường Cầu Ông Lãnh': {'lat': 10.7630, 'lon': 106.6960},
    'Phường Nhiêu Lộc': {'lat': 10.7880, 'lon': 106.6810},
    'Phường Bàn Cờ': {'lat': 10.7720, 'lon': 106.6790},
    'Phường Khánh Hội': {'lat': 10.7580, 'lon': 106.7020},
    'Phường Chợ Quán': {'lat': 10.7530, 'lon': 106.6750},
    'Phường Bình Tiên': {'lat': 10.7490, 'lon': 106.6430},
    'Phường Minh Phụng': {'lat': 10.7570, 'lon': 106.6470},
    'Phường Phú Định': {'lat': 10.7280, 'lon': 106.6210},
    'Phường Chánh Hưng': {'lat': 10.7420, 'lon': 106.6780},
    'Phường Hòa Hưng': {'lat': 10.7790, 'lon': 106.6690},
    'Phường Diên Hồng': {'lat': 10.7690, 'lon': 106.6630},
    # Bình Tân & Tân Phú & Tân Bình
    'Phường An Lạc': {'lat': 10.7320, 'lon': 106.6110},
    'Phường Bình Hưng Hòa': {'lat': 10.7950, 'lon': 106.5940},
    'Phường Phú Thạnh': {'lat': 10.7820, 'lon': 106.6270},
    'Phường Phú Thọ Hòa': {'lat': 10.7890, 'lon': 106.6310},
    # Ngoại thành TP.HCM
    'Xã Đông Thạnh': {'lat': 10.8980, 'lon': 106.6320},
    'Xã Bà Điểm': {'lat': 10.8410, 'lon': 106.5990},
    'Xã Tân Thới Nhì': {'lat': 10.8920, 'lon': 106.5740},
    'Xã Tân Nhựt': {'lat': 10.7130, 'lon': 106.5420},
    'Xã Vĩnh Lộc A': {'lat': 10.8120, 'lon': 106.5640},
    'Xã Bình Hưng': {'lat': 10.7180, 'lon': 106.6730},
    'Xã Phước Kiển': {'lat': 10.7040, 'lon': 106.7020},
    'Xã Cần Giờ': {'lat': 10.5120, 'lon': 106.8790}
}

# ---------------------------------------------------------------------------
# TỌA ĐỘ TUYẾN ĐƯỜNG / PHỐ / ĐIỂM NÓNG Ổ DỊCH (STREET-LEVEL HOTSPOTS)
# ---------------------------------------------------------------------------
STREET_COORDS = {
    'Lê Văn Thọ': {'lat': 10.8418, 'lon': 106.6575, 'ward': 'Phường 11', 'district': 'Gò Vấp', 'province': 'TP. Hồ Chí Minh'},
    'Nguyễn Văn Thương': {'lat': 10.8038, 'lon': 106.7161, 'ward': 'Phường 25', 'district': 'Bình Thạnh', 'province': 'TP. Hồ Chí Minh'},
    'Hoàng Hoa Thám': {'lat': 10.8042, 'lon': 106.6918, 'ward': 'Phường 7', 'district': 'Bình Thạnh', 'province': 'TP. Hồ Chí Minh'},
    'Mai Văn Ngọc': {'lat': 10.7947, 'lon': 106.6755, 'ward': 'Phường 10', 'district': 'Phú Nhuận', 'province': 'TP. Hồ Chí Minh'},
    'Điện Biên Phủ': {'lat': 10.7981, 'lon': 106.7032, 'ward': 'Phường 15', 'district': 'Bình Thạnh', 'province': 'TP. Hồ Chí Minh'},
    'Thanh Đa': {'lat': 10.8322, 'lon': 106.7314, 'ward': 'Phường 27', 'district': 'Bình Thạnh', 'province': 'TP. Hồ Chí Minh'},
    'TCH36': {'lat': 10.8596, 'lon': 106.6184, 'ward': 'Phường Tân Chánh Hiệp', 'district': 'Quận 12', 'province': 'TP. Hồ Chí Minh'},
    'Đường Số 4': {'lat': 10.8432, 'lon': 106.6621, 'ward': 'Phường 11', 'district': 'Gò Vấp', 'province': 'TP. Hồ Chí Minh'},
    'Đường 48': {'lat': 11.3120, 'lon': 106.0990, 'ward': 'Chưa rõ', 'district': 'Chưa xác định', 'province': 'Tây Ninh'},
    'Ấp 5': {'lat': 10.9620, 'lon': 106.8510, 'ward': 'Chưa rõ', 'district': 'Chưa xác định', 'province': 'Đồng Nai'}
}


# ---------------------------------------------------------------------------
# HIERARCHICAL ADDRESS PARSER: PHỐ > PHƯỜNG > QUẬN > TỈNH/THÀNH PHỐ
# ---------------------------------------------------------------------------
def extract_province(address_str):
    """Trích xuất và chuẩn hóa tên Tỉnh / Thành phố."""
    if pd.isna(address_str) or not address_str:
        return None
    address_lower = str(address_str).lower()

    address_lower = address_lower.replace('thành phố hồ chí minh', 'hồ chí minh')
    address_lower = address_lower.replace('tp hồ chí minh', 'hồ chí minh')
    address_lower = address_lower.replace('t.p hồ chí minh', 'hồ chí minh')
    address_lower = address_lower.replace('thành phố thủ đức', 'hồ chí minh')
    address_lower = address_lower.replace('tp thủ đức', 'hồ chí minh')
    address_lower = address_lower.replace('thủ đức', 'hồ chí minh')

    for old_prov in sorted(MERGE_MAP.keys(), key=len, reverse=True):
        if old_prov in address_lower:
            return MERGE_MAP[old_prov]

    return None


def parse_hierarchical_address(address_str):
    """
    Phân tách địa chỉ theo cấu trúc đa tầng:
    Phố (Street) > Phường (Ward) > Quận (District) > Tỉnh/Thành phố (Province).
    Tự động suy luận Quận/Huyện từ Phường/Tuyến phố và gán Tọa độ (lat, lon) chính xác nhất.
    """
    if pd.isna(address_str) or not str(address_str).strip():
        return {
            'street': 'Chưa rõ',
            'ward': 'Chưa rõ',
            'district': 'Chưa xác định',
            'province': 'Chưa xác định',
            'lat': 10.7769,
            'lon': 106.7009,
            'geo_level': 'default'
        }

    addr = str(address_str).strip()
    addr_lower = addr.lower()
    prov = extract_province(addr) or 'Chưa xác định'

    district = 'Chưa xác định'
    ward = 'Chưa rõ'
    street = 'Chưa rõ'

    # 1. Trích xuất Tuyến đường / Phố / Số nhà (Street Level)
    for st_key in STREET_COORDS.keys():
        if st_key.lower() in addr_lower:
            street = st_key
            break

    if street == 'Chưa rõ':
        # Regex tìm các mẫu: 70/14 Lê Văn Thọ, Đường số 4, Ấp 5, v.v.
        st_match = re.search(r'(\d+[\w\/\-]*\s+[^,;]+|\b(?:đường|phố|hẻm|ngõ|ấp|tổ|khu\s+phố)\s+[^,;]+)', addr, re.IGNORECASE)
        if st_match:
            cand_st = st_match.group(1).strip()
            # Loại trừ nếu chuỗi trúng tên Tỉnh hoặc Quận
            if not any(k in cand_st.lower() for k in ['hồ chí minh', 'hà nội', 'tỉnh', 'huyện', 'quận', 'phường', 'thị xã', 'thành phố']):
                street = cand_st.title()

    # 2. Trích xuất Phường / Xã / Thị trấn (Ward Level)
    ward_match = re.search(r'(phường\s+[\w\s\d]+|xã\s+[\w\s\d]+|thị trấn\s+[\w\s\d]+|p\.\s*[\w\s\d]+|x\.\s*[\w\s\d]+)', addr, re.IGNORECASE)
    if ward_match:
        ward = ward_match.group(1).strip().title()

    # 3. Trích xuất Quận / Huyện / Thị xã (District Level)
    for d_k in sorted(HCMC_DISTRICT_COORDS.keys(), key=len, reverse=True):
        pattern = r'\b' + re.escape(d_k.lower()) + r'\b'
        if re.search(pattern, addr_lower):
            district = d_k
            break

    if district == 'Chưa xác định':
        parts = [p.strip() for p in re.split(r'[,;]', addr) if p.strip()]
        for part in reversed(parts):
            lower_p = part.lower()
            if any(p_k in lower_p for p_k in ['thành phố hồ chí minh', 'tp hồ chí minh', 'thành phố hà nội', 'tp hà nội', 'tỉnh', 'tp. hồ chí minh']):
                continue
            if any(kw in lower_p for kw in ['quận', 'huyện', 'thị xã', 'thành phố']):
                district = part.strip().title()
                break
            if re.search(r'^(q\.|q\s*)\d+', lower_p) or re.search(r'^(h\.|h\s*)\w+', lower_p) or re.search(r'^(tx\.|tx\s*)\w+', lower_p):
                district = part.strip().title()
                break

    # 4. Suy luận liên cấp (Inference rules) nếu thiếu Quận hoặc Phường
    ward_clean = re.sub(r'^(phường|xã|thị trấn|p\.|x\.)\s*', '', ward, flags=re.IGNORECASE).lower().strip()
    if district in ['Chưa xác định', 'Tp Hồ Chí Minh', 'Thành Phố Hồ Chí Minh']:
        if ward_clean in HCMC_WARD_TO_DISTRICT:
            district = HCMC_WARD_TO_DISTRICT[ward_clean]
        elif street in STREET_COORDS:
            district = STREET_COORDS[street].get('district', district)
            if ward == 'Chưa rõ':
                ward = STREET_COORDS[street].get('ward', ward)
            if prov == 'Chưa xác định':
                prov = STREET_COORDS[street].get('province', prov)

    if ward == 'Chưa rõ' and street in STREET_COORDS:
        ward = STREET_COORDS[street].get('ward', 'Chưa rõ')

    # 5. Gán tọa độ (lat, lon) và Geo Level theo độ mịn cao nhất
    lat, lon, geo_level = None, None, 'default'

    # Ưu tiên 1: Tọa độ Tuyến Phố (Street)
    if street in STREET_COORDS:
        lat = STREET_COORDS[street]['lat']
        lon = STREET_COORDS[street]['lon']
        geo_level = 'street'

    # Ưu tiên 2: Tọa độ Phường / Xã (Ward)
    if lat is None:
        for w_k, w_coord in WARD_COORDS.items():
            if w_k.lower() in ward.lower() or ward.lower() in w_k.lower():
                lat = w_coord['lat']
                lon = w_coord['lon']
                geo_level = 'ward'
                break

    # Ưu tiên 3: Tọa độ Quận / Huyện (District)
    if lat is None and district in HCMC_DISTRICT_COORDS:
        lat = HCMC_DISTRICT_COORDS[district]['lat']
        lon = HCMC_DISTRICT_COORDS[district]['lon']
        geo_level = 'district'

    # Ưu tiên 4: Tọa độ Tỉnh / Thành phố (Province)
    if lat is None and prov in VN_PROVINCE_COORDS:
        lat = VN_PROVINCE_COORDS[prov]['lat']
        lon = VN_PROVINCE_COORDS[prov]['lon']
        geo_level = 'province'

    # Fallback mặc định (Trung tâm TP.HCM)
    if lat is None or lon is None:
        lat = 10.7769
        lon = 106.7009
        geo_level = 'default'

    return {
        'street': street,
        'ward': ward,
        'district': district,
        'province': prov,
        'lat': round(lat, 6),
        'lon': round(lon, 6),
        'geo_level': geo_level
    }


def extract_district(address_str):
    """Backward compatibility wrapper for extract_district."""
    parsed = parse_hierarchical_address(address_str)
    return parsed['district']


# ---------------------------------------------------------------------------
# PHÂN LOẠI MỨC ĐỘ NGUY CƠ & KHOANH VÙNG Ổ DỊCH (RISK CLASSIFICATION)
# ---------------------------------------------------------------------------
def classify_risk_level(cases: int, level: str = 'ward') -> tuple:
    """
    Phân loại mức độ cảnh báo nguy cơ và gán màu sắc:
    - Vùng Đỏ (Rất cao / Ổ dịch bùng phát)
    - Vùng Cam (Nguy cơ cao)
    - Vùng Vàng (Nguy cơ trung bình)
    - Vùng Xanh (Nguy cơ thấp)
    """
    if level == 'street':
        if cases >= 5:
            return 'Vùng Đỏ (Rất cao)', '#d90429', 500, 'Phun hóa chất diệt muỗi khẩn cấp & khoanh vùng 500m'
        elif cases >= 3:
            return 'Vùng Cam (Nguy cơ cao)', '#f77f00', 300, 'Diệt bọ gậy, giám sát ca bệnh trong bán kính 300m'
        elif cases >= 2:
            return 'Vùng Vàng (Nguy cơ)', '#fcbf49', 200, 'Cảnh báo dịch tễ & vệ sinh môi trường'
        else:
            return 'Vùng Xanh (Kiểm soát)', '#2a9d8f', 100, 'Theo dõi định kỳ'
    elif level == 'ward':
        if cases >= 15:
            return 'Vùng Đỏ (Rất cao)', '#d90429', 1000, 'Báo động đỏ: Triển khai chiến dịch dập dịch toàn phường'
        elif cases >= 8:
            return 'Vùng Cam (Nguy cơ cao)', '#f77f00', 600, 'Tổng vệ sinh triệt để nơi sinh sản của lăng quăng'
        elif cases >= 3:
            return 'Vùng Vàng (Nguy cơ)', '#fcbf49', 300, 'Tăng cường giám sát ổ dịch cục bộ'
        else:
            return 'Vùng Xanh (Kiểm soát)', '#2a9d8f', 150, 'Theo dõi định kỳ'
    else:  # district or province
        if cases >= 50:
            return 'Vùng Đỏ (Rất cao)', '#d90429', 2000, 'Điểm nóng trọng điểm cấp Quận/Huyện'
        elif cases >= 20:
            return 'Vùng Cam (Nguy cơ cao)', '#f77f00', 1200, 'Cảnh báo nguy cơ dịch bùng phát diện rộng'
        elif cases >= 5:
            return 'Vùng Vàng (Nguy cơ)', '#fcbf49', 600, 'Giám sát dịch tễ chặt chẽ'
        else:
            return 'Vùng Xanh (Kiểm soát)', '#2a9d8f', 300, 'Theo dõi định kỳ'


def generate_epidemic_clusters(df_cases_enriched: pd.DataFrame) -> pd.DataFrame:
    """
    Tạo danh sách các Cụm Dịch / Vùng Khoanh Vùng Nhiễm Bệnh (Epidemic Outbreak Clusters)
    từ dữ liệu ca bệnh chi tiết.
    """
    if df_cases_enriched.empty:
        return pd.DataFrame()

    clusters = []

    # 1. Cụm theo Tuyến Phố (Street Hotspots)
    street_valid = df_cases_enriched[df_cases_enriched['street'] != 'Chưa rõ']
    if not street_valid.empty:
        street_agg = street_valid.groupby(
            ['province', 'district', 'ward', 'street', 'lat', 'lon', pd.Grouper(key='date', freq='ME')]
        ).size().reset_index(name='cases')

        for idx, row in street_agg.iterrows():
            risk_lvl, color, radius, reco = classify_risk_level(row['cases'], level='street')
            clusters.append({
                'cluster_id': f"ST_{row['province']}_{row['district']}_{row['street']}_{row['date'].strftime('%Y%m')}",
                'name': f"Tuyến {row['street']} ({row['ward']}, {row['district']})",
                'level': 'Phố / Tuyến đường',
                'province': row['province'],
                'district': row['district'],
                'ward': row['ward'],
                'street': row['street'],
                'date': row['date'],
                'year': row['date'].year,
                'month': row['date'].month,
                'cases': int(row['cases']),
                'risk_level': risk_lvl,
                'risk_color': color,
                'radius_meters': radius,
                'recommendation': reco,
                'lat': row['lat'],
                'lon': row['lon']
            })

    # 2. Cụm theo Phường / Xã (Ward Hotspots)
    ward_valid = df_cases_enriched[df_cases_enriched['ward'] != 'Chưa rõ']
    if not ward_valid.empty:
        ward_agg = ward_valid.groupby(
            ['province', 'district', 'ward', 'lat', 'lon', pd.Grouper(key='date', freq='ME')]
        ).size().reset_index(name='cases')

        for idx, row in ward_agg.iterrows():
            risk_lvl, color, radius, reco = classify_risk_level(row['cases'], level='ward')
            clusters.append({
                'cluster_id': f"WD_{row['province']}_{row['district']}_{row['ward']}_{row['date'].strftime('%Y%m')}",
                'name': f"{row['ward']} ({row['district']})",
                'level': 'Phường / Xã',
                'province': row['province'],
                'district': row['district'],
                'ward': row['ward'],
                'street': 'Tất cả các tuyến phố',
                'date': row['date'],
                'year': row['date'].year,
                'month': row['date'].month,
                'cases': int(row['cases']),
                'risk_level': risk_lvl,
                'risk_color': color,
                'radius_meters': radius,
                'recommendation': reco,
                'lat': row['lat'],
                'lon': row['lon']
            })

    # 3. Cụm theo Quận / Huyện (District Hotspots)
    dist_valid = df_cases_enriched[df_cases_enriched['district'] != 'Chưa xác định']
    if not dist_valid.empty:
        dist_agg = dist_valid.groupby(
            ['province', 'district', pd.Grouper(key='date', freq='ME')]
        ).size().reset_index(name='cases')

        for idx, row in dist_agg.iterrows():
            # Lookup district coords
            d_coord = HCMC_DISTRICT_COORDS.get(row['district'], {})
            d_lat = d_coord.get('lat', VN_PROVINCE_COORDS.get(row['province'], {}).get('lat', 10.7769))
            d_lon = d_coord.get('lon', VN_PROVINCE_COORDS.get(row['province'], {}).get('lon', 106.7009))
            risk_lvl, color, radius, reco = classify_risk_level(row['cases'], level='district')
            clusters.append({
                'cluster_id': f"DT_{row['province']}_{row['district']}_{row['date'].strftime('%Y%m')}",
                'name': f"{row['district']}, {row['province']}",
                'level': 'Quận / Huyện',
                'province': row['province'],
                'district': row['district'],
                'ward': 'Tất cả các phường',
                'street': 'Toàn quận',
                'date': row['date'],
                'year': row['date'].year,
                'month': row['date'].month,
                'cases': int(row['cases']),
                'risk_level': risk_lvl,
                'risk_color': color,
                'radius_meters': radius,
                'recommendation': reco,
                'lat': d_lat,
                'lon': d_lon
            })

    return pd.DataFrame(clusters)


# ---------------------------------------------------------------------------
# CORE DATA PROCESSING FUNCTION
# ---------------------------------------------------------------------------
def process_patient_data(source_path_or_dir):
    """
    Đọc và xử lý dữ liệu bệnh nhân từ 1 file, nhiều file hoặc thư mục.
    Bóc tách cấu trúc đa tầng: Phố > Phường > Quận > Tỉnh/Thành phố.
    Tạo các bảng tổng hợp và dữ liệu khoanh vùng dịch tễ.
    """
    target_files = []
    if isinstance(source_path_or_dir, (list, tuple)):
        target_files = [Path(p) for p in source_path_or_dir if Path(p).exists()]
    else:
        p = Path(source_path_or_dir)
        if p.is_dir():
            target_files = sorted(list(p.glob("*.xlsx")) + list(p.glob("*.xls")) + list(p.glob("*.csv")))
        elif p.exists():
            target_files = [p]

    if not target_files:
        logger.warning(f"No valid patient files found in: {source_path_or_dir}")
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

    logger.info(f"Loading patient data from {len(target_files)} file(s)...")
    all_cases = []

    for file_path in target_files:
        logger.info(f"  Reading: {file_path.name}...")
        if file_path.suffix.lower() == ".csv":
            try:
                df = pd.read_csv(file_path)
                sheets_data = [("csv", df)]
            except Exception as e:
                logger.warning(f"  Error reading CSV {file_path}: {e}")
                continue
        else:
            try:
                xls = pd.ExcelFile(file_path)
                sheets_data = []
                for s in xls.sheet_names:
                    if s.lower().startswith("ma icd"):
                        continue
                    sheets_data.append((s, pd.read_excel(file_path, sheet_name=s)))
            except Exception as e:
                logger.warning(f"  Error reading Excel {file_path}: {e}")
                continue

        for sheet_name, df in sheets_data:
            missing = REQUIRED_COLUMNS - set(df.columns)
            if missing:
                logger.warning(
                    f"File '{file_path.name}' Sheet '{sheet_name}' is missing expected column(s) {missing} - skipping."
                )
                continue

            col_map = {
                'NgayVao': 'date',
                'NgayRa': 'discharge_date',
                'Diachi': 'address',
                'NamSinh': 'birth_year',
                'Maicd': 'icd_code',
                'TenBenhNhan': 'patient_name'
            }
            df = df.rename(columns=col_map)
            df = df.dropna(subset=['date'])
            df['date'] = pd.to_datetime(df['date'], errors='coerce')
            df = df.dropna(subset=['date'])

            # Lọc mã ICD SXH
            combined_tag = f"{file_path.stem} {sheet_name}".lower()
            is_dedicated_dengue = any(k in combined_tag for k in ['xuất huyết', 'xuat huyet', 'data'])
            if not is_dedicated_dengue and 'icd_code' in df.columns:
                df['icd_code'] = df['icd_code'].astype(str)
                df = df[df['icd_code'].str.contains('A90|A97', na=False)]

            all_cases.append(df)

    if not all_cases:
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

    combined_df = pd.concat(all_cases, ignore_index=True)

    # Khử trùng lặp bệnh nhân đa file
    dedup_cols = ['patient_name', 'birth_year', 'address', 'date']
    avail_dedup = [c for c in dedup_cols if c in combined_df.columns]
    if avail_dedup:
        initial_len = len(combined_df)
        combined_df = combined_df.drop_duplicates(subset=avail_dedup)
        logger.info(f"Deduplication complete: {initial_len} -> {len(combined_df)} unique patient records.")

    # -----------------------------------------------------------------------
    # BÓC TÁCH HIERARCHY: PHỐ > PHƯỜNG > QUẬN > TỈNH/THÀNH PHỐ + TỌA ĐỘ
    # -----------------------------------------------------------------------
    parsed_info = combined_df['address'].apply(parse_hierarchical_address).tolist()
    parsed_df = pd.DataFrame(parsed_info)

    combined_df['province'] = parsed_df['province']
    combined_df['district'] = parsed_df['district']
    combined_df['ward'] = parsed_df['ward']
    combined_df['street'] = parsed_df['street']
    combined_df['lat'] = parsed_df['lat']
    combined_df['lon'] = parsed_df['lon']
    combined_df['geo_level'] = parsed_df['geo_level']

    # Bỏ qua dòng không xác định được Tỉnh
    combined_df = combined_df.dropna(subset=['province'])
    combined_df = combined_df[combined_df['province'] != 'Chưa xác định']

    # 1. Tổng hợp cấp Tỉnh / Thành phố
    combined_df_prov = combined_df.copy()
    combined_df_prov.set_index('date', inplace=True)
    agg_prov = combined_df_prov.groupby(['province', pd.Grouper(freq='ME')]).size().reset_index(name='cases')

    # 2. Tổng hợp cấp Quận / Huyện
    combined_df_dist = combined_df.copy()
    combined_df_dist.set_index('date', inplace=True)
    agg_dist = combined_df_dist.groupby(['province', 'district', pd.Grouper(freq='ME')]).size().reset_index(name='cases')

    # 3. Tổng hợp cấp Phường / Xã
    combined_df_ward = combined_df.copy()
    combined_df_ward.set_index('date', inplace=True)
    agg_ward = combined_df_ward.groupby(
        ['province', 'district', 'ward', 'lat', 'lon', pd.Grouper(freq='ME')]
    ).size().reset_index(name='cases')

    # 4. Tổng hợp cấp Tuyến Phố / Điểm Nóng
    combined_df_street = combined_df[combined_df['street'] != 'Chưa rõ'].copy()
    if not combined_df_street.empty:
        combined_df_street.set_index('date', inplace=True)
        agg_street = combined_df_street.groupby(
            ['province', 'district', 'ward', 'street', 'lat', 'lon', pd.Grouper(freq='ME')]
        ).size().reset_index(name='cases')
    else:
        agg_street = pd.DataFrame()

    # 5. Sinh Cụm Dịch & Khoanh Vùng Nhiễm Bệnh
    clusters_df = generate_epidemic_clusters(combined_df)

    return agg_prov, agg_dist, agg_ward, agg_street, clusters_df


def load_population_data(pop_file_path):
    logger.info(f"Loading population data from {pop_file_path}...")
    pop_df = pd.read_csv(pop_file_path)

    pop_df['ADM1_EN_lower'] = pop_df['ADM1_EN'].str.lower()
    import unicodedata

    def strip_accents(s):
        s = s.replace('đ', 'd').replace('Đ', 'd')
        return ''.join(c for c in unicodedata.normalize('NFD', s) if unicodedata.category(c) != 'Mn')

    def map_eng_to_new(name):
        name_clean = strip_accents(name).replace(' city', '').replace(' province', '').strip()
        for k, v in MERGE_MAP.items():
            k_clean = strip_accents(k).replace(' city', '').replace(' province', '').strip()
            if k_clean == name_clean or k == name_clean:
                return v
        return None

    pop_df['province'] = pop_df['ADM1_EN_lower'].apply(map_eng_to_new)
    pop_agg = pop_df.groupby('province')['T_TL'].sum().reset_index(name='population')

    return pop_agg


def load_and_process_new_data(patient_file, pop_file):
    """
    Quy trình tích hợp toàn diện: Tỉnh > Quận > Phường > Tuyến phố > Cụm dịch khoanh vùng.
    Lưu trữ đầy đủ các tệp dữ liệu vào MongoDB và Local CSV.
    """
    res = process_patient_data(patient_file)
    if len(res) == 5:
        cases_df, dist_df, ward_df, street_df, clusters_df = res
    else:
        cases_df, dist_df = res[0], res[1]
        ward_df, street_df, clusters_df = pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

    pop_df = load_population_data(pop_file)

    if cases_df.empty:
        return cases_df

    # 1. Tỉnh
    merged = pd.merge(cases_df, pop_df, on='province', how='left')
    merged['incidence_rate'] = (merged['cases'] / merged['population']) * 100000
    merged['incidence_rate'] = merged['incidence_rate'].fillna(0)
    merged['year'] = merged['date'].dt.year
    merged['month'] = merged['date'].dt.month

    paths.PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    # 2. Quận / Huyện
    if not dist_df.empty:
        dist_merged = pd.merge(dist_df, pop_df, on='province', how='left')
        dist_merged['incidence_rate'] = (dist_merged['cases'] / dist_merged['population']) * 100000
        dist_merged['incidence_rate'] = dist_merged['incidence_rate'].fillna(0)
        dist_merged['year'] = dist_merged['date'].dt.year
        dist_merged['month'] = dist_merged['date'].dt.month

        # Gán tọa độ quận
        def lookup_dist_lat(row):
            if row['district'] in HCMC_DISTRICT_COORDS:
                return HCMC_DISTRICT_COORDS[row['district']]['lat']
            return VN_PROVINCE_COORDS.get(row['province'], {}).get('lat', 10.7769)

        def lookup_dist_lon(row):
            if row['district'] in HCMC_DISTRICT_COORDS:
                return HCMC_DISTRICT_COORDS[row['district']]['lon']
            return VN_PROVINCE_COORDS.get(row['province'], {}).get('lon', 106.7009)

        dist_merged['lat'] = dist_merged.apply(lookup_dist_lat, axis=1)
        dist_merged['lon'] = dist_merged.apply(lookup_dist_lon, axis=1)

        if mongo_data_service:
            mongo_data_service.save_dataset("district_breakdown", dist_merged, paths.DISTRICT_CSV)
        else:
            dist_merged.to_csv(paths.DISTRICT_CSV, index=False)
        logger.info(f"Saved district breakdown ({len(dist_merged)} rows) to {paths.DISTRICT_CSV}")

        # HCMC Hotspots
        hcmc_df = dist_merged[dist_merged['province'] == 'TP. Hồ Chí Minh'].copy()
        if not hcmc_df.empty:
            if mongo_data_service:
                mongo_data_service.save_dataset("hcmc_hotspots", hcmc_df, paths.HCMC_HOTSPOTS_CSV)
            else:
                hcmc_df.to_csv(paths.HCMC_HOTSPOTS_CSV, index=False)
            logger.info(f"Saved HCMC hotspots ({len(hcmc_df)} rows) to {paths.HCMC_HOTSPOTS_CSV}")

    # 3. Phường / Xã
    if not ward_df.empty:
        ward_df['year'] = ward_df['date'].dt.year
        ward_df['month'] = ward_df['date'].dt.month
        ward_df['risk_level'] = ward_df['cases'].apply(lambda c: classify_risk_level(c, level='ward')[0])
        ward_csv_path = getattr(paths, 'WARD_CSV', paths.PROCESSED_DIR / "ward_breakdown.csv")
        if mongo_data_service:
            mongo_data_service.save_dataset("ward_breakdown", ward_df, ward_csv_path)
        else:
            ward_df.to_csv(ward_csv_path, index=False)
        logger.info(f"Saved ward breakdown ({len(ward_df)} rows) to {ward_csv_path}")

    # 4. Tuyến Phố / Đường
    if not street_df.empty:
        street_df['year'] = street_df['date'].dt.year
        street_df['month'] = street_df['date'].dt.month
        street_df['risk_level'] = street_df['cases'].apply(lambda c: classify_risk_level(c, level='street')[0])
        street_csv_path = getattr(paths, 'STREET_HOTSPOTS_CSV', paths.PROCESSED_DIR / "street_hotspots.csv")
        if mongo_data_service:
            mongo_data_service.save_dataset("street_hotspots", street_df, street_csv_path)
        else:
            street_df.to_csv(street_csv_path, index=False)
        logger.info(f"Saved street hotspots ({len(street_df)} rows) to {street_csv_path}")

    # 5. Cụm Dịch & Khoanh Vùng Nhiễm Bệnh
    if not clusters_df.empty:
        clusters_csv_path = getattr(paths, 'EPIDEMIC_CLUSTERS_CSV', paths.PROCESSED_DIR / "epidemic_clusters.csv")
        if mongo_data_service:
            mongo_data_service.save_dataset("epidemic_clusters", clusters_df, clusters_csv_path)
        else:
            clusters_df.to_csv(clusters_csv_path, index=False)
        logger.info(f"Saved epidemic clusters ({len(clusters_df)} rows) to {clusters_csv_path}")

    return merged


def merge_weather_features(df_cases: pd.DataFrame,
                            df_weather: pd.DataFrame) -> pd.DataFrame:
    """Ghép nối đặc trưng thời tiết độ trễ 1 tháng."""
    if df_weather is None or df_weather.empty:
        logger.warning("No weather data provided — filling weather features with 0.")
        df_cases = df_cases.copy()
        df_cases['rain_lag_1']     = 0.0
        df_cases['temp_lag_1']     = 0.0
        df_cases['humidity_lag_1'] = 0.0
        return df_cases

    import unicodedata

    def strip_vn(s: str) -> str:
        s = s.replace('đ', 'd').replace('Đ', 'D')
        return ''.join(
            c for c in unicodedata.normalize('NFD', s)
            if unicodedata.category(c) != 'Mn'
        ).lower().strip()

    weather = df_weather.copy()
    weather['_prov_key'] = weather['province'].apply(strip_vn)

    df_out = df_cases.copy()
    df_out['_prov_key'] = df_out['province'].apply(strip_vn)

    weather = weather.sort_values(['_prov_key', 'year', 'month'])
    weather['rain_lag_1']     = weather['precipitation_sum']
    weather['temp_lag_1']     = weather['temp_mean']
    weather['humidity_lag_1'] = weather['humidity_mean']

    weather['join_year']  = weather['year']
    weather['join_month'] = weather['month'] + 1
    weather.loc[weather['join_month'] > 12, 'join_year']  += 1
    weather.loc[weather['join_month'] > 12, 'join_month']  = 1

    lag_cols = weather[['_prov_key', 'join_year', 'join_month',
                         'rain_lag_1', 'temp_lag_1', 'humidity_lag_1']].copy()
    lag_cols = lag_cols.rename(columns={'join_year': 'year', 'join_month': 'month'})

    df_out = pd.merge(df_out, lag_cols, on=['_prov_key', 'year', 'month'], how='left')
    df_out.drop(columns=['_prov_key'], inplace=True)
    df_out[['rain_lag_1', 'temp_lag_1', 'humidity_lag_1']] = \
        df_out[['rain_lag_1', 'temp_lag_1', 'humidity_lag_1']].fillna(0.0)

    n_matched = (df_out['rain_lag_1'] != 0).sum()
    n_total   = len(df_out)
    logger.info(f"Weather features merged: {n_matched}/{n_total} rows matched "
                f"({n_matched/n_total*100:.1f}%)")

    return df_out


if __name__ == "__main__":
    res = load_and_process_new_data(paths.RAW_DATA_FILE, paths.POP_DATA_FILE)
    print("Sample output:")
    print(res.head())
    paths.PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    res.to_csv(paths.HISTORICAL_CSV, index=False)