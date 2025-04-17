# This python script helps to break down the object contributes to data+bss and text memory usage in a map file
# So you'll know who is the main eater of the resource
import sys
import re
from collections import defaultdict

def parse_map(filename):
    """
    Parse .map file and return two dicts: 
    { object_path: data_bss_size_in_bytes }
    { object_path: text_size_in_bytes }
    Handles both single-line entries and two-line (section-only + continuation) entries,
    and ignores any lines containing 'load address'.
    """
    data_bss_contrib = defaultdict(int)
    text_contrib = defaultdict(int)
    pending_section = False
    pending_section_type = None

    # 1) full inline entries: .data.foo  addr  size  obj
    inline_re = re.compile(
        r'^\s*\.([a-zA-Z0-9_\.]+)\s+0x[0-9A-Fa-f]+\s+0x([0-9A-Fa-f]+)\s+(\S+)'
    )
    # 2) section-only lines:   .bss.PHY_Object
    section_only_re = re.compile(
        r'^\s*\.([a-zA-Z0-9_\.]+)\s*$'
    )
    # 3) continuation lines:    addr  size  obj
    cont_re = re.compile(
        r'^\s*0x[0-9A-Fa-f]+\s+0x([0-9A-Fa-f]+)\s+(\S+)'
    )

    with open(filename, 'r') as f:
        for line in f:
            # skip any 'load address' lines
            if 'load address' in line:
                pending_section = False
                continue

            # 1) try full inline
            m = inline_re.match(line)
            if m:
                section = m.group(1)
                size = int(m.group(2), 16)
                obj = m.group(3)
                
                if size:
                    if section.startswith('data') or section.startswith('bss'):
                        data_bss_contrib[obj] += size
                    elif section.startswith('text'):
                        text_contrib[obj] += size
                
                pending_section = False
                continue

            # 2) try section-only
            m = section_only_re.match(line)
            if m:
                section = m.group(1)
                if section.startswith('data') or section.startswith('bss'):
                    pending_section = True
                    pending_section_type = 'data_bss'
                elif section.startswith('text'):
                    pending_section = True
                    pending_section_type = 'text'
                else:
                    pending_section = False
                continue

            # 3) if we had a pending section, try continuation
            if pending_section:
                m2 = cont_re.match(line)
                if m2:
                    size = int(m2.group(1), 16)
                    obj = m2.group(2)
                    
                    if size:
                        if pending_section_type == 'data_bss':
                            data_bss_contrib[obj] += size
                        elif pending_section_type == 'text':
                            text_contrib[obj] += size
                
                pending_section = False
                continue

            # otherwise, reset pending flag
            pending_section = False

    return data_bss_contrib, text_contrib


def print_section_report(contrib, section_name):
    sorted_items = sorted(contrib.items(), key=lambda kv: kv[1], reverse=True)
    
    print(f"{section_name + ' (bytes)':>16}   Object")
    print(f"{'-'*16}   {'-'*40}")
    
    total_size = 0
    for obj, sz in sorted_items:
        total_size += sz
        print(f"{sz:16,d}   {obj}")
    
    print(f"{'-'*16}   {'-'*40}")
    print(f"Total {section_name} Size: {total_size:,d}")
    print()


def main():
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} <path/to/your.map>")
        sys.exit(1)

    data_bss_contrib, text_contrib = parse_map(sys.argv[1])
    
    # Print data+bss report
    print("\n=== DATA + BSS SECTION USAGE ===")
    print_section_report(data_bss_contrib, "data+bss")
    
    # Print text report
    print("=== TEXT SECTION USAGE ===")
    print_section_report(text_contrib, "text")

if __name__ == '__main__':
    main()