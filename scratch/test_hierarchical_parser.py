import re
import pandas as pd
from pathlib import Path
from src.data_processor import MERGE_MAP, extract_province

# Mapping known wards in HCMC to their districts
HCMC_WARD_TO_DISTRICT = {
    'an phú đông': 'Quận 12',
    'thới an': 'Quận 12',
    'tân chánh hiệp': 'Quận 12',
    'hiệp thành': 'Quận 12',
    'tân thới nhất': 'Quận 12',
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
    'tân thới nhứt': 'Quận 12',
    'hóc môn': 'Hóc Môn',
    'củ chi': 'Củ Chi',
    'nhà bè': 'Nhà Bè',
    'bình chánh': 'Bình Chánh',
    'cần giờ': 'Cần Giờ'
}

with open('scratch/all_unique_addrs.txt', 'r', encoding='utf-8') as f:
    unique_addrs = [l.strip() for l in f if l.strip()]

def parse_address_test(addr_str):
    if not addr_str or not isinstance(addr_str, str):
        return {'street': 'Chưa rõ', 'ward': 'Chưa rõ', 'district': 'Chưa xác định', 'province': 'Chưa xác định'}
    
    addr = addr_str.strip()
    prov = extract_province(addr) or 'Chưa xác định'
    
    district = 'Chưa xác định'
    ward = 'Chưa rõ'
    street = 'Chưa rõ'
    
    # Check street indicators first (e.g. 70/14 Lê Văn Thọ, 82/10 Điện Biên Phủ, 1/50/1/8 Thanh Đa)
    street_match = re.search(r'(\d+[\w\/\-]*\s+[^,;]+|\b(?:đường|phố|hẻm|ngõ|ấp|tổ|khu\s+phố|tổ\s+dân\s+phố)\s+[^,;]+)', addr, re.IGNORECASE)
    if street_match:
        cand_street = street_match.group(1).strip()
        if not any(k in cand_street.lower() for k in ['thành phố hồ chí minh', 'tp hồ chí minh', 'tỉnh', 'huyện', 'quận', 'phường', 'thị xã', 'thành phố']):
            street = cand_street.title()
        elif re.search(r'^\d+[\w\/\-]*\s+[^\,]+', cand_street):
            street = cand_street.title()
            
    # Look for Ward
    ward_match = re.search(r'(phường\s+[\w\s\d]+|xã\s+[\w\s\d]+|thị trấn\s+[\w\s\d]+|p\.\s*[\w\s\d]+|x\.\s*[\w\s\d]+)', addr, re.IGNORECASE)
    if ward_match:
        ward = ward_match.group(1).strip().title()
        
    # Look for District
    dist_match = re.search(r'(quận\s+\w+|q\.\s*\w+|huyện\s+[\w\s]+|thị xã\s+[\w\s]+|thành phố\s+[\w\s]+|tp\.\s*[\w\s]+)', addr, re.IGNORECASE)
    if dist_match:
        cand_d = dist_match.group(1).strip().title()
        if not any(cand_d.lower() == p.lower() or p.lower() in cand_d.lower() for p in ['thành phố hồ chí minh', 'tp hồ chí minh', 'tp. hồ chí minh', 'thành phố hà nội', 'tp hà nội']):
            district = cand_d
            
    # Infer district from ward if district is missing or generic (especially for HCMC)
    if district in ['Chưa xác định', 'Tp Hồ Chí Minh', 'Thành Phố Hồ Chí Minh']:
        ward_clean = re.sub(r'^(phường|xã|thị trấn|p\.|x\.)\s*', '', ward, flags=re.IGNORECASE).lower().strip()
        if ward_clean in HCMC_WARD_TO_DISTRICT:
            district = HCMC_WARD_TO_DISTRICT[ward_clean]
        elif 'lê văn thọ' in addr.lower():
            district = 'Gò Vấp'
            street = 'Lê Văn Thọ'
            ward = 'Phường 11'
        elif 'điện biên phủ' in addr.lower():
            district = 'Bình Thạnh'
            street = 'Điện Biên Phủ'
            ward = 'Phường 15'
        elif 'thanh đa' in addr.lower():
            district = 'Bình Thạnh'
            street = 'Bình Quới - Thanh Đa'
            ward = 'Phường 27'
        elif 'hoàng hoa thám' in addr.lower():
            district = 'Bình Thạnh'
            street = 'Hoàng Hoa Thám'
            ward = 'Phường 7'
        elif 'mai văn ngọc' in addr.lower():
            district = 'Phú Nhuận'
            street = 'Mai Văn Ngọc'
            ward = 'Phường 10'
        elif 'nguyễn văn thương' in addr.lower():
            district = 'Bình Thạnh'
            street = 'Nguyễn Văn Thương'
            ward = 'Phường 25'
        elif 'tch36' in addr.lower() or 'tân chánh hiệp' in addr.lower():
            district = 'Quận 12'
            street = 'TCH36'
            ward = 'Phường Tân Chánh Hiệp'
            
    return {'raw': addr, 'street': street, 'ward': ward, 'district': district, 'province': prov}

res = [parse_address_test(a) for a in unique_addrs]
df_res = pd.DataFrame(res)
print('Parsed Summary:')
print('Provinces identified:', (df_res['province'] != 'Chưa xác định').sum(), '/', len(df_res))
print('Districts identified:', (df_res['district'] != 'Chưa xác định').sum(), '/', len(df_res))
print('Wards identified:', (df_res['ward'] != 'Chưa rõ').sum(), '/', len(df_res))
print('Streets identified:', (df_res['street'] != 'Chưa rõ').sum(), '/', len(df_res))
print('\nSample Parsed Records:')
for _, r in df_res.head(25).iterrows():
    print(f"Raw: '{r['raw']}' -> Pho: '{r['street']}' | Phuong: '{r['ward']}' | Quan: '{r['district']}' | Tinh: '{r['province']}'")
