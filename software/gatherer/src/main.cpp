#include <string>
#include <chrono>

#include <gatherer.h>

void sleep(const double s) {

  std::this_thread::sleep_for(std::chrono::milliseconds(int(s * 1000)));
}

int main(int argc, char* argv[]) {

  std::string serial_port_file;
  int         baud_rate;
  bool        serial_port_virtual;
  std::string data_path;
  std::string data_path_meta;
  int         frame_count;
  uint16_t    frame_duration;
  uint8_t     frame_mode;
  int         frame_mode_input;

  if (argc == 9) {

    serial_port_file    = argv[1];
    baud_rate           = atoi(argv[2]);
    serial_port_virtual = atoi(argv[3]);
    data_path           = argv[4];
    data_path_meta      = argv[5];
    frame_count         = atoi(argv[6]);
    frame_duration      = atoi(argv[7]);
    frame_mode_input    = atoi(argv[8]);
    if(frame_mode_input == 0) {
      printf("Frame mode: TOA_TOT\n");
      frame_mode = LLCP_TPX3_PXL_MODE_TOA_TOT;
    } else if(frame_mode_input == 1) {
      printf("Frame mode: TOA\n");
      frame_mode = LLCP_TPX3_PXL_MODE_TOA;
    } else if(frame_mode_input == 2) {
      printf("Frame mode: TOT\n");
      frame_mode = LLCP_TPX3_PXL_MODE_MPX_ITOT;
    } else {
      printf("Invalid frame mode\n");
      return 0;
    }

    printf(
        "loaded params: \n \
serial port: '%s'\n \
baud rate: '%d'\n \
serial port is: '%s'\n \
output data path: '%s'\n \
frame count: '%d'\n \
frame duration: '%d'\n \
frame mode: '%s'\n",
        serial_port_file.c_str(), baud_rate, serial_port_virtual ? "virtual" : "real", data_path.c_str(), frame_count, frame_duration, argv[7]);
  } else {
    printf("params not supplied!\n");
    printf("required: ./gatherer <serial port file> <baud rate> <serial port virtual ? true : false> <output data path> <frame count> <frame duration> <frame mode>\n");
    return 0;
  }

  data_path_meta = data_path +; 

  // initialize the gatherer
  Gatherer gatherer(data_path, data_path_meta);

  // open the serial line
  gatherer.connect(serial_port_file, baud_rate, serial_port_virtual);

  printf("getting status\n");
  gatherer.getStatus();

  // --------------------------------------------------------------
  // |        IMPORTANT, ADD SLEEPS BETWEEN EVERY COMMANDS        |
  // --------------------------------------------------------------
  sleep(0.01);

  printf("powering on\n");
  gatherer.pwr(true);

  sleep(0.01);

  // | ------------------ pixel masking example ----------------- |
  /*
  printf("masking pixels\n");
  int square_size = 20;
  for (int i = 128 - int(square_size / 2.0); i < 128 + int(square_size / 2.0); i++) {
    for (int j = 245 - int(square_size / 2.0); j < 245 + int(square_size / 2.0); j++) {

      bool state = true;

      gatherer.maskPixel(i, j, state);
      printf("%s pixel x: %d, y: %d\n", state ? "masking" : "unmasking", i, j);
    }
  }

  // the configuration needs to be reloaded to apply the pixel mask
  printf("setting configuration preset 0\n");
  */

  // | ---------------- setting threshold example --------------- |
  /*
  printf("setting threshold");
  gatherer.setThreshold(333, 555);
  */

  sleep(0.01);

  printf("getting temperature\n");
  gatherer.getTemperature();

  sleep(0.01);

  // | ----------- measure ---------- |
  for (int i = 0; i < frame_count; i++) {
    
    printf("measuring frame\n");
    gatherer.measureFrame(frame_duration, frame_mode);
    sleep(0.01);
  }

 

  printf("powering off\n");
  gatherer.pwr(false);

  // this will stop the threads and disconnect the uart
  gatherer.stop();

  printf("finished\n");

  return 0;
}
