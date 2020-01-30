#include <Windows.h>
#include <iostream>
#include <fstream>
#include <string>
#include <ctime>
#include <sys/timeb.h>
#include <stdio.h>
#include <dirent.h>

#define KEY_DOWN(VK_NONAME) ((GetAsyncKeyState(VK_NONAME) & 0x8000) ? 1:0)

using namespace std;

const int CHAR_ARRAY_SIZE = 16384;
const int RANDOM_MIDTIME = 1500;
const int RANDOM_TIME_RANGE = 1000;

int client_width = 1920;
int client_height = 1080;
int browser_address_bar_x = 365;
int browser_address_bar_y = 51;

string dir_separator = "\\";
string root_path = ""; // "C:\\Entrobus\\projects\\crawl\\20190214scrapy\\tt\\dianping\\";
string detailed_folder = "detail_html_fiddler";
string fiddler_detailed_file_path = "";
int fiddler_detailed_file_number = 0;
string shop_id_file = "";

string get_cwd(void)  
{
	char exeFullPath[MAX_PATH];
	string strPath = "";
	GetModuleFileName(NULL,exeFullPath,MAX_PATH);
	strPath = (string)exeFullPath;
	int pos = strPath.find_last_of('\\', strPath.length()); // this is for Windows, todo: for Linux
	string path = strPath.substr(0, pos);
	return path;
}

int get_file_number(string path)
{
	int counter = 0;
	DIR *dir;
	struct dirent *ptr;
	dir = opendir(path.c_str());
	while( ( ptr = readdir(dir) ) != NULL )
	{
		counter++;
	}
	closedir(dir);
	return counter - 2;
}

int get_random_time(int midtime = 0, int range = 0)
{
	srand( time(0) );
	if ( 1 > midtime )
	{
		midtime = RANDOM_MIDTIME;
	}
	if ( 1 > range )
	{
		range = RANDOM_TIME_RANGE;
	}
	if ( range > midtime )
	{
		midtime = range;
	}
	return midtime - range / 2 + rand() % range;
	// rand() returns an int from 0 to RAND_MAX(2147483647)
}

double get_current_ts()  
{
	double x, y;
	timeb t;
	ftime(&t);
	return t.time + t.millitm / 1000;
}

// https://www.cnblogs.com/xuan52rock/p/6061155.html
// https://zhidao.baidu.com/question/647698977954822045.html
BOOL copy_to_clipboard( string data_to_clipboard )
{
	if(OpenClipboard(NULL))
	{
		EmptyClipboard();
		HGLOBAL clipbuffer;
		char *buffer;
		const char *pszData = data_to_clipboard.c_str();
		clipbuffer = GlobalAlloc(GMEM_DDESHARE, data_to_clipboard.length() + 1 );
		buffer = (char *)GlobalLock(clipbuffer);
		strcpy(buffer, pszData);
		GlobalUnlock(clipbuffer);
		SetClipboardData(CF_TEXT, clipbuffer);
		CloseClipboard();
		return TRUE;
	}
	return FALSE;
}

void ctrl_paste( int x = 0, int y = 0 )
{
	mouse_event(MOUSEEVENTF_ABSOLUTE|MOUSEEVENTF_MOVE, x*65535/client_width, y*65535/client_height, 0, 0);
	Sleep(15);
	mouse_event(MOUSEEVENTF_LEFTDOWN,0,0,0,0);
	Sleep(5);
	mouse_event(MOUSEEVENTF_LEFTUP,0,0,0,0);
	Sleep(10);

	keybd_event(0x11,0,0,0); // CTRL key
	keybd_event(0x41,0,0,0); // A key
	keybd_event(0x41,0,2,0);
	keybd_event(0x11,0,2,0);
	Sleep(10);

	keybd_event(0x2E,0,0,0); // DEL key
	keybd_event(0x2E,0,2,0);
	Sleep(20);

	keybd_event(0x11,0,0,0); // CTRL key
	keybd_event(0x56,0,0,0); // V key
	keybd_event(0x56,0,2,0);
	keybd_event(0x11,0,2,0);
	Sleep(20);

	keybd_event(0x23,0,0,0); // END key
	keybd_event(0x23,0,2,0);
	Sleep(20);

	keybd_event(0x0D,0,0,0); // Enter Key
	keybd_event(0x0D,0,2,0);
}

int wait_for_detailed_html_file( int sleep_time = 5000, int minimal_interval = 200 )
{
	int new_time = 0;
	char esc_key = 0x1B;
	double end_ts = 0.0;
	int current_file_number = 0;
	int counter = 0;
	int minimal_interval_range = 0;

	if ( 1 > sleep_time )
	{
		new_time = get_random_time(0, 0); // in case that 0 > sleep_time
	} else {
		new_time = get_random_time(sleep_time, 0);
	}
	end_ts = get_current_ts() + new_time / 1000;

	if ( 100 > minimal_interval){
		minimal_interval = 100;
	}
	minimal_interval_range = minimal_interval / 2;
	
	while( 1 ){
		if ( 0 != sleep_time && end_ts < get_current_ts()  ){
			break;
		}
		if( KEY_DOWN(esc_key) ){
			cout << "you pressed esc." << endl;
			return -1;
		}
		if ( 0 == counter % 25 ){
			// check file in every 0.5 second; once newly downloaded file is found, do not wait
			current_file_number = get_file_number( fiddler_detailed_file_path );
			if ( fiddler_detailed_file_number < current_file_number ){
				// fiddler_detailed_file downloaded
				Sleep( get_random_time(minimal_interval, minimal_interval_range) );
				fiddler_detailed_file_number = current_file_number;
				break;
			} else {
				cout << "current_file_number = " << current_file_number << endl;
			}
		}
		counter++;
		Sleep(20);
	}
	return 0;
}

void read_file_and_crawl( int sleep_time = 5000, int minimal_interval = 200 )
{
	string filepath = root_path + shop_id_file;
	char buffer[CHAR_ARRAY_SIZE];
	string temp, url;
	fstream out;
	BOOL result = FALSE;
	int esc_detector = 0;
	int counter = 0;

	out.open( filepath, ios::in|ios::binary );
	while (!out.eof())
	{
		out.getline(buffer, CHAR_ARRAY_SIZE, '\n');
		temp = buffer;
		if ( 5 < sizeof(buffer) && 5 < temp.length() )
		{
			url = "http://www.dianping.com/shop/" + temp;
			result = copy_to_clipboard( url );
			if ( result ){
				Sleep( 100 );
				cout << "crawling " << url << endl;
				counter++;
				ctrl_paste( 365, 51 );
				esc_detector = wait_for_detailed_html_file( sleep_time, minimal_interval );
				if ( -1 == esc_detector ){
					break;
				}
			} else {
				cout << "cannot open Clipboard while crawling " << url << endl;
				break;
			}
		}
	}
	out.close();
	cout << counter << " requests sent."<< endl;
}

int main(int argc,char *argv[])
{
	/*
	This program is the C++ code for requesting webpages like the one at http://www.dianping.com/shop/68129347
	It will read the shop_id.txt file that contains all shop_ids like 68129347, then mouse click the address
	bar of your browser, press Ctrl + A, press DELETE, press Ctrl + V, and then Enter keys. Then the program will 
	monitor the file numbers in detail_html_fiddler folder. Once it find out that folder has one more file than 
	previous check, it will do the next cycle to crawl the next webpage like http://www.dianping.com/shop/98005572
	The first argument can bypass such a detection.
	After compiling, you are suggestted to rename the default exe file name from a.exe to hotel.exe and then
	use this commandline "hotel.exe 1000 150 365 51 detail_html_fiddler shop_id.txt" to run the exe file. After
	running this commandline, you shall activate your browser window in 5 seconds.
	Meaning of these arguments:
	1000: 	Depending on your Internet Bandwidth and download speed, you can set differnt time gap between
			two adjacent cycles. The program will wait upto 1.000 second; if after 1 second, the file number in
			detail_html_fiddler folder has NOT increase, it will give up this shop_id and crawl the next shop_id.
	150: 	To avoid DOS attack, we place a 0.1 second minimal between two adjacent cycles. You can change this to
			0.150 second or other values.
	365:	the x value of your browser address bar
	51:		the y value of your browser address bar
	detail_html_fiddler:	the folder name to which fiddler will save the newly crawl html file
	shop_id.txt:			The file name that store all shop_ids to be crawled.
	*/
	root_path = get_cwd();
	root_path = root_path + dir_separator;
	detailed_folder = "detail_html_fiddler";
	shop_id_file = "shop_id.txt";
	int sleep_time = 5000;
	int minimal_interval = 200;
	string temp = "";

	if ( 1 < argc && -1 < atoi( argv[1] ) ){
		sleep_time = atoi(argv[1]);
		// 0 means will wait until detailed html file downloaded
	}
	if ( 2 < argc && 0 < atoi( argv[2] ) ){
		minimal_interval = atoi(argv[2]);
	}
	if ( 3 < argc && 0 < atoi( argv[3] ) ){
		browser_address_bar_x = atoi(argv[3]); // 365
	}
	if ( 4 < argc && 0 < atoi( argv[4] ) ){
		browser_address_bar_y = atoi(argv[4]); // 51
	}
	if ( 5 < argc ){
		temp = argv[5];
		if ( 2 < temp.length() ){
			detailed_folder = temp;
		} else {
			cout << "detailed_folder shall be 3 characters or more" << endl;
			return -1;
		}
	}
	if ( 6 < argc ){
		temp = argv[6];
		if ( 4 < temp.length() ){
			shop_id_file = temp;
		} else {
			cout << "shop_id_file shall be 5 characters or more; like shop_id.txt" << endl;
			return -1;
		}
	}
	cout << "sleep_time = " << sleep_time << "; minimal_interval = " << minimal_interval << endl;
	cout << "browser_address_bar_x = " << browser_address_bar_x << "; browser_address_bar_y = " << browser_address_bar_y << endl;
	cout << "detailed_folder = " << detailed_folder << "; shop_id_file = " << shop_id_file << endl << endl;
	fiddler_detailed_file_path = root_path + detailed_folder + dir_separator;
	fiddler_detailed_file_number = get_file_number( fiddler_detailed_file_path );
	Sleep( 5000 );
	read_file_and_crawl( sleep_time, minimal_interval );
	return 0;
}
