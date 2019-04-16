import io,os,struct,glob,codecs,math,re,sys,zlib

def eboot_bin_auth(fn_eboot,key):
    fp_s=open(fn_eboot,'rb')
    data=bytearray(fp_s.read())
    fp_s.close()
    data[0x80:0x88]=key
    
    fp_s=open(fn_eboot,'wb')
    fp_s.write(data)
    fp_s.close()
def txt_ps3_to_vita(path_txt,path_save):
    rootdir = path_txt
    f_list = os.listdir(rootdir)
    for i in range(0,len(f_list)):
        if f_list[i].find('.unknown') < 0 :
            continue
        fn_s = os.path.join(rootdir,f_list[i])
        fn = fn_s.replace('.unknown','.elzma')      
        
        fl_s=open(fn_s,'rb')
        data=fl_s.read()
        fl_s.close()
        
        fl=open(fn,'wb')
        fl.write(struct.pack('<I',len(data)))
        dst=zlib.compress(data)
        fl.write(struct.pack('<I',len(dst)))
        fl.write(b'\x00\x00\x00\x00\x00\x00\x00\x00')
        fl.write(dst)
        fl.close()
def eboot_txt_import(fn_elf,path_txt,fn_save):
    fp_s=open(fn_elf,'rb')
    buf=bytearray(fp_s.read())
    fp_s.close()
    
    EBOOT_OFFSET = 0x80FFFF40
    EBOOT_DATA_OFFSET = 0x81000E00
    EBOOT_INDEX = 0x76574
    
    #OFFSET = 0x81600000
    OFFSET = 0x8113DB00
    pos = EBOOT_INDEX
    #cur_pos, = struct.unpack("<I", buf[pos+4:pos+8])
    cur_pos = OFFSET

    rootdir = path_txt
    num = 0
    #f_list = os.listdir(rootdir)
    while True:
        name_offset, data_offset, uncomp_size, block_size = struct.unpack("<4I", buf[pos:pos+0x10])
        if (name_offset == 0) : 
            break
        
        cpos = name_offset-EBOOT_OFFSET
        name = struct.unpack("<1s", buf[cpos:cpos+1])[0]
        while True:
            cpos += 1
            n = struct.unpack("<1s", buf[cpos:cpos+1])[0]
            if n == b'\x00' :
                break;
            name += n
        name = name.decode()
        #if name == '5400_bnr' : #跳转到码表后方区域
        #    cur_pos = OFFSET
        name = rootdir+'/'+name+'.elzma'
        fl=open(name,'rb')
        data=fl.read()
        fl.close()
        file_comp_size = len(data)
        file_uncomp_size,= struct.unpack("<I", data[0:4])
        buf[pos+4:pos+0x10] = struct.pack("<3I", cur_pos, file_uncomp_size, file_comp_size)
        buf[cur_pos-EBOOT_DATA_OFFSET:cur_pos-EBOOT_DATA_OFFSET+file_comp_size] = data
        print("Import ok %d,%d->%d,%d  %s,%x" % (uncomp_size, block_size, file_uncomp_size, file_comp_size, name, cur_pos-EBOOT_DATA_OFFSET))
        cur_pos += file_comp_size
        #buf[cur_pos-EBOOT_DATA_OFFSET:cur_pos-EBOOT_DATA_OFFSET+0x20] = bytes(0x20)
        #cur_pos += 0x20
        '''while (cur_pos-EBOOT_DATA_OFFSET)%0x10 !=0 :
            buf[cur_pos-EBOOT_DATA_OFFSET] = b'\x00'
            cur_pos += 1'''
        pos += 0x10
        num += 1


    fp_s=open(fn_save,'wb')
    fp_s.write(buf)
    fp_s.close()
    
def eboot_elf_build(fn_elf,font2_data,png_data,fn_save):
    fp_s=open(fn_elf,'rb')
    data=bytearray(fp_s.read())
    fp_s.close()
    #./readelf -l eboot.bin.EDIT.elf
    ELF_HEAD=0xC0
    
    #------------------------------------------------
    # LOAD2尾部增长，写入数据
    '''
    ELF_SIZE_ADD=1000
    LOAD_SIZE,=struct.unpack("<I",data[0x64:0x68])
    LOAD_SIZE+=ELF_SIZE_ADD
    data[0x64:0x68]=struct.pack("<I", LOAD_SIZE)#LOAD2 FileSize

    ELF_SIZE,=struct.unpack("<I",data[0x78:0x7C])
    data_end=data[ELF_SIZE:]
    data=data[:ELF_SIZE]
    data += bytes(ELF_SIZE_ADD)
    data[0x78:0x7C]=struct.pack("<I", ELF_SIZE+ELF_SIZE_ADD)
    '''
    # wchdsk(@wch9627)提供的具体地址
    #------------------------------------------------
    # 字库1（大字库）写入
    FONT1_SIZE_POS = 0x34A6 + ELF_HEAD
    FONT1_SIZE_POS2 = 0x3544 + ELF_HEAD
    FONT1_OFFSET_POS_L = 0x34B4 + ELF_HEAD
    FONT1_OFFSET_POS_H = 0x34BE + ELF_HEAD


    FONT1_SIZE=b'\x41\xF6\x2E\x60'# MOVW            R0, #0x1E2E
    FONT1_SIZE2=b'\x41\xF6\x2E\x61'# MOVW            R1, #0x1E2E
    # Font num is 3863
    FONT1_OFFSET_L=b'\x4B\xF6\x40\x17'# MOVW            R7, #0xB940
    FONT1_OFFSET_H=b'\xC8\xF2\x13\x17'# MOVT.W          R7, #0x8113
    # FileOffset is 0x44F600   VirtAddr is 0x8144F600
    data[FONT1_SIZE_POS:FONT1_SIZE_POS+4]=FONT1_SIZE
    data[FONT1_SIZE_POS2:FONT1_SIZE_POS2+4]=FONT1_SIZE2

    data[FONT1_OFFSET_POS_L:FONT1_OFFSET_POS_L+4]=FONT1_OFFSET_L
    data[FONT1_OFFSET_POS_H:FONT1_OFFSET_POS_H+4]=FONT1_OFFSET_H

    SRC_FONT1_POS=0x6EF4C+ELF_HEAD
    SRC_FONT1_SIZE=0x1524

    #FONT1_POS=0x478000-0xE00
    FONT1_POS=0x13B940-0xE00
    FONT1_NUM=3863
    data[FONT1_POS:FONT1_POS+10000]=bytes(10000)
    data[FONT1_POS:FONT1_POS+SRC_FONT1_SIZE]=data[SRC_FONT1_POS:SRC_FONT1_POS+SRC_FONT1_SIZE]
    pos=FONT1_POS+SRC_FONT1_SIZE
    font_num=FONT1_NUM-SRC_FONT1_SIZE/2
    font_code=0xf043
    while font_num > 0 : 
        if (font_code & 0xff) < 0x40 : 
            font_code+=1
            continue
        data[pos:pos+2]=struct.pack(">H", font_code)
        font_code+=1
        font_num-=1
        pos+=2
    
    #------------------------------------------------
    # elf head patch
    # LOAD1尾部增长，写入自定义函数
    LOAD_ADD_SIZE=0x12
    ADD_POS,=struct.unpack("<I",data[0x44:0x48])
    LOAD_SIZE = ADD_POS + LOAD_ADD_SIZE
    data[0x44:0x48]=struct.pack("<I", LOAD_SIZE)#LOAD1 FileSize
    data[0x48:0x4C]=struct.pack("<I", LOAD_SIZE)#LOAD1 FileSize
    
    #------------------------------------------------
    # 字库2（小字库）写入
    # function code
    SUB_POS = ADD_POS+ELF_HEAD + 4 #0x810790C4
    SUB_BIN=b'\x10\xB5\x40\xF2\x86\x10\xE8\xF7\x25\xF8\x10\xBD'
    data[SUB_POS:SUB_POS+len(SUB_BIN)]=SUB_BIN
    '''
    By DeQxJ00
    
    810790C0 ，PUSH	{R4, LR}		,0x10B5  
    810790C2 ，MOV	R0, #0x186	,0x40F28610
    810790C6 ，BL	sub_81061118	,0xE8F725F8
    810790D0 ，POP	{R4, PC}		,0x10BD
    '''
    #call function code
    CALL_POS=0x34F2+ELF_HEAD
    CALL_BIN=b'\x75\xF0\xE7\xFD'
    data[CALL_POS:CALL_POS+4] = CALL_BIN
    '''
    By DeQxJ00
    
    810034F2	,  BL	#0x810790C4	,0x75F0E7FD
    '''

    #font2 size2 and position
    FONT2_SIZE_POS2 = 0x3556 + ELF_HEAD
    FONT2_OFFSET_POS_L = 0x34FC + ELF_HEAD
    FONT2_OFFSET_POS_H = 0x3506 + ELF_HEAD

    FONT2_SIZE2=b'\x10\xF5\xC3\x71'# ADDS.W          R1, R0, #0x186
    FONT2_OFFSET_L=b'\x4D\xF6\x80\x06'# MOVW            R6, #0xD880
    FONT2_OFFSET_H=b'\xC8\xF2\x13\x16'# MOVT.W          R6, #0x8113

    data[FONT2_SIZE_POS2:FONT2_SIZE_POS2+4] = FONT2_SIZE2

    data[FONT2_OFFSET_POS_L:FONT2_OFFSET_POS_L+4]=FONT2_OFFSET_L
    data[FONT2_OFFSET_POS_H:FONT2_OFFSET_POS_H+4]=FONT2_OFFSET_H

    #font2 data
    #FONT2_POS=0x479F40-0xE00
    FONT2_POS=0x13D880-0xE00
    FONT2_NUM=195
    #font2_data=open('font2.bin','rb').read()
    data[FONT2_POS:FONT2_POS+len(font2_data)]=font2_data
    
    #------------------------------------------------
    #警告图片写入
    #warning picture
    PNG_POS=0x863E0
    PNG_SIZE=0x349C0
    #png_data=open('warning_in.gxt','rb').read()
    data[PNG_POS:PNG_POS+PNG_SIZE] = png_data

    #------------------------------------------------

    fp_s=open(fn_save,'wb')
    fp_s.write(data)
    #fp_s.write(data_end)
    fp_s.close()
if __name__ == "__main__":

    if sys.argv[1] == '-build':
        eboot_elf_build(sys.argv[2],open(sys.argv[3], "rb").read(),open(sys.argv[4], "rb").read(),sys.argv[5])
    elif sys.argv[1] == '-txtc':
        txt_ps3_to_vita(sys.argv[2],sys.argv[3])
    elif sys.argv[1] == '-txti':
        eboot_txt_import(sys.argv[2],sys.argv[3],sys.argv[4])
    elif sys.argv[1] == '-auth':
        eboot_bin_auth(sys.argv[2],open(sys.argv[3], "rb").read(8))



