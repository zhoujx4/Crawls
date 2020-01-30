Date: 20190520(Revision 2), 20190517(Revision 1)
Description: This project (crawls) is created by Peter for code version controlling of all crawls developed by Peter and other co-workers. Inside this folder, there is a scrapy project named tt and it includes several spiders. Each spider will run on its own.
Some spiders are ONLY for parsing the files in html and/or other formats. These files are crawled using different tools such as fiddler, FSCapture, and others.

Spider Dianping in Project tt
Such files include codes written in C++, JScript, Python, and other languages. These files are described as these following:

./crawls/tt/dianping/cpp/ctrl_end.cpp:
This program is the C++ code for pressing Ctrl + END keys and then mouse click "Next Page" Button on a webpage like the one at http://www.dianping.com/yueyang/ch10/g104
	After compiling, you are suggestted to rename the default exe file name from a.exe to ctrl.exe and then	use this commandline "ctrl.exe 98 1750 1184 576" to run the exe file. After running this commandline, you shall activate your browser window in 5 seconds. Meaning of these arguments:
	98: 	In a single cycle, the program will hit ctrl + END and left click mouse 1 time; 98 means the program will run 98 cycles.
	1750: 	Depending on your Internet Bandwidth and download speed, you can set differnt time gap between two adjacent cycles. 1750 means 1.75 seconds
	1184:	the x value of the "Next Page" Button after Ctrl + End is hit
	576:	the y value of the "Next Page" Button after Ctrl + End is hit

./crawls/tt/dianping/cpp/hotel.cpp:		
This program is the C++ code for requesting webpages like the one at http://www.dianping.com/shop/68129347. It will read the shop_id.txt file that contains all shop_ids like 68129347, then mouse click the address bar of your browser, press Ctrl + A, press DELETE, press Ctrl + V, and then Enter keys. Then the program will monitor the file numbers in detail_html_fiddler folder. Once it find out that folder has one more file than previous check, it will do the next cycle to crawl the next webpage like http://www.dianping.com/shop/98005572. The first argument can bypass such a detection.
	After compiling, you are suggestted to rename the default exe file name from a.exe to hotel.exe and then use this commandline "hotel.exe 1000 150 365 51 detail_html_fiddler shop_id.txt" to run the exe file. After running this commandline, you shall activate your browser window in 5 seconds. Meaning of these arguments:
	1000: 	Depending on your Internet Bandwidth and download speed, you can set differnt time gap between two adjacent cycles. The program will wait upto 1.000 second; if after 1 second, the file number in detail_html_fiddler folder has NOT increase, it will give up this shop_id and crawl the next shop_id.
	150: 	To avoid DOS attack, we place a 0.1 second minimal between two adjacent cycles. You can change this to 0.150 second or other values.
	365:	the x value of your browser address bar
	51:		the y value of your browser address bar
	detail_html_fiddler:	the folder name to which fiddler will save the newly crawl html file
	shop_id.txt:			The file name that store all shop_ids to be crawled.

./crawls/tt/dianping/cpp/page_down.cpp:	
This program is the C++ code for requesting webpages like the one at http://www.dianping.com/guangzhou/ch70/g27813. These webpages appear no "Next Page" button after Ctrl + END is hit. We use PageDown Button instead. After compiling, you are suggestted to rename the default exe file name from a.exe to page.exe and then use this commandline "page.exe 98 1750 3 1266 790" to run the exe file. After running this commandline, you shall activate your browser window in 5 seconds. Meaning of these arguments:
	98: 	In a single cycle, the program will hit PageDown Key several times and left click mouse 1 time; 98 means the program will run 98 cycles.
	1750: 	Depending on your Internet Bandwidth and download speed, you can set differnt time gap between two adjacent cycles. 1750 means 1.75 seconds
	3: 		In a single cycle, the program will hit Ctrl + HOME once and then PageDown Key 3 times.
	1266:	the x value of the "Next Page" Button after Ctrl + End is hit
	790:	the y value of the "Next Page" Button after Ctrl + End is hit

./crawls/tt/dianping/cpp/points.cpp:
This program is the C++ code for display the x and y values of your mouse. After compiling, you are suggestted to rename the default exe file name from a.exe to pts.exe and then use this commandline "pts.exe 3 5000" to run the exe file. After running this commandline, you shall move your mouse to the point you want to collect the x and y values in 2 seconds. Meaning of these arguments:
	3: 		The program will run 3 cycles.
	5000: 	Depending on the speed you move your mouse, you can set differnt time gap between two adjacent cycles. 5000 means 5 seconds

Crawl Easygo
./easygo/main.py
As of 20190501 the Tencent Server is detecting the browser driver proviously used, we now have to use an actural browser like Chrome, Edge, Firefox, 360, Opera, or another. After setting up the requeired 3 files (./easygo/input/tasks.txt, ./easygo/input/cookie_temp_example.txt, and ./easygo/input/internal_cookies_pool.txt), run this commandline: python main.py to start crawling assigned area (in ./easygo/input/tasks.txt). 

After finishing requesting all json files in folder ./easygo/jsons, set up file ./easygo/input/arguments.ini corrently, and then run this commandline:
python make_data.py -a filename=arguments.ini -m run_parser
if your data looks good but there was some interrupts during crawling, then run the following one:
python make_data.py -a filename=arguments.ini -m read_single_line_and_write_ok_zero
after setting run_purpose = 2 in [yyyymmddread_single_line_and_write_ok_zero] section of file ./easygo/input/arguments.ini where yyyymmdd represents today.

if you missed some requests during crawling, then run the following one:
python make_data.py -a filename=arguments.ini -m read_single_line_and_write_ok_zero
after setting run_purpose = 1 in [yyyymmddread_single_line_and_write_ok_zero] section of file ./easygo/input/arguments.ini where yyyymmdd represents today.
The Method read_single_line_and_write_ok_zero will generate one file in ./easygo/results folder, and you can render this file using the js_render package provided by Zeng Ji.

Notes:
1. You are suggested to compile All C++ codes using MinGW; download the correct version of MinGW for your platform (Windows 64, 32, Linux, and others), install it, and use g++ xxx.cpp -std=c++11 commandline to compile these codes.
