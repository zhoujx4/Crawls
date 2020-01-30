"""
Abandoned: 繁琐，采用https://my.oschina.net/u/2396236/blog/1798170
Author: 深入学习python解析并读取PDF文件内容的方法https://www.cnblogs.com/wj-1314/p/9429816.html
"""
import pyocr
import importlib
import sys
import time
 
importlib.reload(sys)
time1 = time.time()
 
import os.path
from pdfminer.pdfparser import  PDFParser,PDFDocument
from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.converter import PDFPageAggregator
from pdfminer.layout import LTTextBoxHorizontal, LAParams, LTFigure
from pdfminer.pdfinterp import PDFTextExtractionNotAllowed
 
root_path = os.getcwd()
filename = "附件1建（构）筑物建设项目规划条件.pdf"
pdf_file_path = os.path.join( root_path, "inputs", filename )
 
def parse( pdf_file_path = "" ):
	'''解析PDF文本，并保存到TXT文件中'''
	fp = open(pdf_file_path,'rb')
	#用文件对象创建一个PDF文档分析器
	parser = PDFParser(fp)
	#创建一个PDF文档
	doc = PDFDocument()
	#连接分析器，与文档对象
	parser.set_document(doc)
	doc.set_parser(parser)
 
	#提供初始化密码，如果没有密码，就创建一个空的字符串
	doc.initialize()

	#检测文档是否提供txt转换，不提供就忽略
	if not doc.is_extractable:
		raise PDFTextExtractionNotAllowed
	else:
		#创建PDF，资源管理器，来共享资源
		rsrcmgr = PDFResourceManager()
		#创建一个PDF设备对象
		laparams = LAParams()
		device = PDFPageAggregator(rsrcmgr,laparams=laparams)
		#创建一个PDF解释其对象
		interpreter = PDFPageInterpreter(rsrcmgr,device)

		pages = doc.get_pages()
		print( pages )
		print( type(pages) )
 
		#循环遍历列表，每次处理一个page内容
		# doc.get_pages() 获取page列表
		for page in doc.get_pages():
			interpreter.process_page(page)
			#接受该页面的LTPage对象
			layout = device.get_result()
			# 这里layout是一个LTPage对象 里面存放着 这个page解析出的各种对象
			# 一般包括LTTextBox, LTFigure, LTImage, LTTextBoxHorizontal 等等
			# 想要获取文本就获得对象的text属性，

			for x in layout:
				if isinstance(x,LTTextBoxHorizontal):
					with open(r'2.txt','a') as f:
						results = x.get_text()
						print(results)
						f.write(results  +"\n")
				print( f"type == {type(x)}; x == {x}" )
				if lt_image.stream:
					file_stream = lt_image.stream.get_rawdata()
					file_ext = determine_image_type(file_stream[0:4])
				if file_ext:
				file_name = ''.join([str(page_number), '_', lt_image.name, file_ext])
				if write_file(images_folder, file_name, lt_image.stream.get_rawdata(), flags='wb'):
				result = file_name
				if isinstance(x, LTFigure):
					print( dir(x) )
					x_laparams = LAParams()
					x.analyze(x_laparams)
					break

def pdf2pic(path, pic_path):
	"""
	Abandoned: 繁琐，采用https://my.oschina.net/u/2396236/blog/1798170
	revision: 20190802
	Author: https://blog.csdn.net/qq_15969343/article/details/81673302
	从pdf中提取图片
	:param path: pdf的路径
	:param pic_path: 图片保存的路径
	"""
	t0 = time.clock()
	# 使用正则表达式来查找图片
	checkXO = r"/Type(?= */XObject)" 
	checkIM = r"/Subtype(?= */Image)"

	# 打开pdf
	doc = fitz.open(path)
	# 图片计数
	imgcount = 0
	lenXREF = doc._getXrefLength()
 
	# 打印PDF的信息
	print("文件名:{}, 页数: {}, 对象: {}".format(path, len(doc), lenXREF - 1))
	print( type(doc) ) # <class 'fitz.fitz.Document'>
	print( dir(doc) )
	# ['FontInfos', 'FormFonts', 'Graftmaps', 'ShownPages', '__class__', '__del__', '__delattr__', '__dict__', '__dir__', '__doc__', '__eq__', '__format__', '__ge__', 
	# '__getattribute__', '__getitem__', '__gt__', '__hash__', '__init__', '__init_subclass__', '__le__', '__len__', '__lt__', '__module__', '__ne__', '__new__', 
	# '__reduce__', '__reduce_ex__', '__repr__', '__setattr__', '__sizeof__', '__str__', '__subclasshook__', '__swig_destroy__', '__weakref__', 
	
	# '_addFormFont', '_delToC', '_delXmlMetadata', '_deleteObject', '_deletePage', '_do_links', '_dropOutline', '_embeddedFileAdd', '_embeddedFileDel', '_embeddedFileGet', 
	# '_embeddedFileIndex', '_embeddedFileInfo', '_embeddedFileNames', '_embeddedFileUpd', '_forget_page', '_getCharWidths', '_getGCTXerrcode', '_getGCTXerrmsg', '_getMetadata', 
	# '_getNewXref', '_getOLRootNumber', '_getPDFfileid', '_getPDFroot', '_getPageInfo', '_getPageObjNumber', '_getPageXref', '_getTrailerString', '_getXmlMetadataXref', 
	# '_getXrefLength', '_getXrefStream', '_getXrefString', '_graft_id', '_hasXrefOldStyle', '_hasXrefStream', '_loadOutline', '_make_page_map', '_move_copy_page', 
	# '_newPage', '_outline', '_page_refs', '_remove_links_to', '_reset_page_refs', '_setMetadata', '_updateObject', '_updateStream', 

	# 'authenticate', 'close', 'convertToPDF', 'copyPage', 'deletePage', 'deletePageRange', 'embeddedFileAdd', 'embeddedFileCount', 'embeddedFileDel', 'embeddedFileGet', 
	# 'embeddedFileInfo', 'embeddedFileNames', 'embeddedFileUpd', 'extractFont', 'extractImage', 'findBookmark', 'fullcopyPage', 'getCharWidths', 'getPageFontList', 
	# 'getPageImageList', 'getPagePixmap', 'getPageText', 'getSigFlags', 'getToC', 'initData', 'insertPDF', 'insertPage', 'isClosed', 'isDirty', 'isEncrypted', 'isFormPDF', 
	# 'isPDF', 'isReflowable', 'isStream', 'layout', 'loadPage', 'makeBookmark', 'metadata', 'movePage', 'name', 'needsPass', 'newPage', 'openErrCode', 'openErrMsg', 'outline', 
	# 'pageCount', 'permissions', 'resolveLink', 'save', 'saveIncr', 'searchPageFor', 'select', 'setMetadata', 'setToC', 'stream', 'this', 'thisown', 'write']

	# 遍历每一个对象
	page_count = doc.pageCount
	print( f"page_count == {page_count}" )
	for i in range(page_count):
		image_list = doc.getPageImageList(i)
		print( image_list ) # [[5, 0, 1653, 2338, 8, 'DeviceRGB', '', 'JI2a', 'DCTDecode']]

		# all_images = doc.extractImage(i)
		# print( all_images ) # {'ext': 'jpeg', 'smask': 0, 'width': 1653, 'height': 2338, 'colorspace': 3, 'xres': 96, 'yres': 96, 'cs-name': 'DeviceRGB', 'image': b'...'}
		# 定义对象字符串
		# text = doc.getObjectString(i)
		# isXObject = re.search(checkXO, text)
		# # 使用正则表达式查看是否是图片
		# isImage = re.search(checkIM, text)
		# # 如果不是对象也不是图片，则continue
		# if not isXObject or not isImage:
		# 	continue
		imgcount += 1
		print( f"i == {i}; type == {type(i)}" )
		# 根据索引生成图像
		pix = doc.getPagePixmap(doc, int(i+1), matrix=doc[i+1], alpha=False)
		# pix = fitz.Pixmap(doc, i)
		print( f"i == {i}; pix == {pix}; type = {type(pix)}" )
		# 根据pdf的路径生成图片的名称
		new_name = path.replace('\\', '_') + "_img{}.png".format(imgcount)
		new_name = new_name.replace(':', '')

		# 如果pix.n<5,可以直接存为PNG
		if pix.n < 5:
			pix.writePNG(os.path.join(pic_path, new_name))
		# 否则先转换CMYK
		else:
			pix0 = fitz.Pixmap(fitz.csRGB, pix)
			pix0.writePNG(os.path.join(pic_path, new_name))
			pix0 = None
		# 释放资源
		pix = None
		t1 = time.clock()
		print("运行时间:{}s".format(t1 - t0))
		print("提取了{}张图片".format(imgcount))
		print( dir(pix) )

if __name__ == '__main__':
	parse(pdf_file_path)
	time2 = time.time()
	print("总共消耗时间为:",time2-time1)