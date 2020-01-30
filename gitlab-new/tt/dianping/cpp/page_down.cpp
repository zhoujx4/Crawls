#include <iostream>
#include <string>
#include <windows.h>
#include <winuser.h>
#include <ctime>
#include <sys/timeb.h>

#define KEY_DOWN(VK_NONAME) ((GetAsyncKeyState(VK_NONAME) & 0x8000) ? 1:0)

using namespace std;

const int RANDOM_MIDTIME = 1500;
const int RANDOM_TIME_RANGE = 1000;
int client_width = 1920;
int client_height = 1080;

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

void keyboard_scroll_home_or_end(bool y_down = true)
{
	if ( y_down )
	{
		keybd_event(0x11,0,0,0); // CTRL key
		keybd_event(0x23,0,0,0); // END key
		keybd_event(0x23,0,2,0);
		keybd_event(0x11,0,2,0);
	} else {
		keybd_event(0x11,0,0,0); // CTRL key
		keybd_event(0x24,0,0,0); // Home key
		keybd_event(0x24,0,2,0);
		keybd_event(0x11,0,2,0);
	}
	Sleep(50);
}

void keyboard_page_down_or_up( bool y_down = true)
{
	if ( y_down )
	{
		keybd_event(0x22,0,0,0); // PAGE DOWN key
		keybd_event(0x22,0,2,0);
	} else {
		keybd_event(0x21,0,0,0); // PAGE UP key
		keybd_event(0x21,0,2,0);
	}
	Sleep( get_random_time(50, 30) );
}

double get_current_ts()  
{
	double x, y;
	timeb t;
	ftime(&t);
	return t.time + t.millitm / 1000;
}

int click(int x = 0, int y = 0, int sleep_time = 5000, int page_down_key_times = 3)
{
	int new_time = 0;
	int j = 0;
	char esc_key = 0x1B;
	double end_ts = 0.0;
	
	keyboard_scroll_home_or_end(false);
	for (j = 0; j < page_down_key_times; j++ ){
		keyboard_page_down_or_up(true);
		cout << j << endl;
	}
	mouse_event(MOUSEEVENTF_ABSOLUTE|MOUSEEVENTF_MOVE, x*65535/client_width, y*65535/client_height, 0, 0);
	// mouse_event(MOUSEEVENTF_LEFTDOWN,0,0,0,0);
	// mouse_event(MOUSEEVENTF_LEFTUP,0,0,0,0);
	// if( KEY_DOWN(VK_LBUTTON) ){
	// 	cout << "mouse_event MOUSEEVENTF_LEFTCLICK" << endl;
	// }
	
	if ( 1 > sleep_time )
	{
		new_time = get_random_time(0, 0); // in case that 0 > sleep_time
	} else {
		new_time = get_random_time(sleep_time, 0);
	}
	end_ts = get_current_ts() + new_time / 1000;

	while( 1 ){
		if ( get_current_ts() > end_ts ){
			break;
		}
		if( KEY_DOWN(esc_key) ){
			cout << "you pressed esc." << endl;
			return -1;
		}
		Sleep(20);
	}

	return new_time;
}

void initialize_screen_size(void)
{
	HWND hd = GetDesktopWindow();
	RECT rect;
	GetClientRect(hd, &rect);
	client_width = (rect.right - rect.left);
	client_height = (rect.bottom - rect.top); // 1920,1080
}

int main(int argc,char *argv[])
{
	/*
	This program is the C++ code for requesting webpages like the one at http://www.dianping.com/guangzhou/ch70/g27813. 
	These webpages appear no "Next Page" button after Ctrl + END is hit. We use PageDown Button instead. After compiling, 
	you are suggestted to rename the default exe file name from a.exe to page.exe and then use this commandline 
	"page.exe 98 1750 3 1266 790" to run the exe file. After running this commandline, you shall activate your browser 
	window in 5 seconds. Meaning of these arguments:
	98: 	In a single cycle, the program will hit PageDown Key several times and left click mouse 1 time; 98 means the program will run 98 cycles.
	1750: 	Depending on your Internet Bandwidth and download speed, you can set differnt time gap between two adjacent cycles. 1750 means 1.75 seconds
	3: 		In a single cycle, the program will hit Ctrl + HOME once and then PageDown Key 3 times.
	1266:	the x value of the "Next Page" Button after Ctrl + End is hit
	790:	the y value of the "Next Page" Button after Ctrl + End is hit
	*/
	int number_of_pages = 1;
	int page_down_key_times = 3;
	int i = 0, x = 1285, y = 305; // 1270 to 1288; 300 to 306
	int sleep_time = 5000;
	int new_time = 0;
	
	initialize_screen_size();
	
	if ( 1 < argc && 0 < atoi( argv[1] ) ){
		number_of_pages = atoi(argv[1]);
	}
	if ( 2 < argc && 0 < atoi( argv[2] ) ){
		sleep_time = atoi(argv[2]);
	}
	if ( 3 < argc && 0 < atoi( argv[3] ) ){
		page_down_key_times = atoi(argv[3]);
	}
	if ( 4 < argc && 0 < atoi( argv[4] ) ){
		x = atoi(argv[4]);
	}
	if ( 5 < argc && 0 < atoi( argv[5] ) ){
		y = atoi(argv[5]);
	}

	Sleep( 5000 );
	for ( i = 0; i < number_of_pages; i++ )
	{
		new_time = click(x, y, sleep_time, page_down_key_times);
		if ( -1 == new_time ){
			break;
		}
		cout << "clicked Page #" << i << ": slept " << new_time << " seconds." << endl;
	}
	return 0;
}
