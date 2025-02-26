/* ------------------------------------------------------------------------------------------------*
*  Reference: https://docs.datagnss.com/gnss/qzs6c_l6_receiver/ 
*  the origin python version: https://github.com/yoronneko/qzsl6tool/blob/main/python/alstread.py
* -------------------------------------------------------------------------------------------------*
*/

#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>
#include <stdbool.h>
#include <signal.h>

// checksum
void calculate_checksum(const uint8_t* payload, size_t len, uint8_t* csum1, uint8_t* csum2) {
    *csum1 = 0;
    *csum2 = 0;
    for (size_t i = 0; i < len; i++) {
        *csum1 = (*csum1 + payload[i]) & 0xff;
        *csum2 = (*csum1 + *csum2) & 0xff;
    }
}

// Allystar receiver struct
typedef struct {
    int dict_snr[256];        // SNR
    uint8_t dict_data[256][252];  // data
    uint32_t last_gpst;       // last GPS time
    uint8_t l6[252];          // L6 message
    
    // current message 
    uint16_t prn;
    uint16_t gpsw;
    uint32_t gpst;
    uint8_t snr;
    uint8_t data[252];
    char err[32];

    uint16_t p_prn;           // selected satellite PRN
    uint8_t p_snr;            // selected satellite SNR
 
} AllystarReceiver;

// initialize receiver
void init_receiver(AllystarReceiver* rcv) {
    memset(rcv, 0, sizeof(AllystarReceiver));
}

// read data
bool read_data(AllystarReceiver* rcv) {
    uint8_t sync[4] = {0};
    uint8_t b;
  
    
    // find sync byte
    while (1) {
        if (fread(&b, 1, 1, stdin) != 1) {
            return false;
        }
        memmove(sync, sync + 1, 3);
        sync[3] = b;
        if (sync[0] == 0xf1 && sync[1] == 0xd9 && 
            sync[2] == 0x02 && sync[3] == 0x10) {
            break;
        }
    }

    uint8_t l6[268];  // total length 268 bytes
    uint8_t csum[2];

    // declare required variables
    uint16_t len_l6;
    uint8_t freqid;
    uint8_t len_data;
    uint8_t flag;
    
    l6[0] = 0x02;
    l6[1] = 0x10;
    if (fread(l6 + 2, 1, 266, stdin) != 266) {
        return false;
    }
    
    // 读取校验和
    if (fread(csum, 1, 2, stdin) != 2) {
        return false;
    }


    len_l6    = l6[2] | (l6[3] << 8);        // little-endian
    rcv->prn  = (l6[4] | (l6[5] << 8)) - 700;  // little-endian
    freqid    = l6[6];                        // little-endian
    len_data  = l6[7] - 2;                    // little-endian
    rcv->gpsw = (l6[8] << 8) | l6[9];         // big-endian
    rcv->gpst = (l6[10] << 24) | (l6[11] << 16) | (l6[12] << 8) | l6[13];  // big-endian
    rcv->snr  = l6[14];                       // big-endian
    flag      = l6[15];                       // big-endian
    
    // self.data = l6[16:268]
    memcpy(rcv->data, l6 + 16, 252);

    // initialize last_gpst
    if (rcv->last_gpst == 0) {
        rcv->last_gpst = rcv->gpst;
    }

    // error check
    rcv->err[0] = '\0';
    uint8_t csum1, csum2;
    calculate_checksum(l6, 268, &csum1, &csum2);
    
    if (csum[0] != csum1 || csum[1] != csum2) strcat(rcv->err, "CS ");
    if (len_l6 != 264) strcat(rcv->err, "Payload ");
    if (len_data != 63) strcat(rcv->err, "Data ");
    if (flag & 0x01) strcat(rcv->err, "RS ");
    if (flag & 0x02) strcat(rcv->err, "Week ");
    if (flag & 0x04) strcat(rcv->err, "TOW ");

    return true;
}

void select_sat(AllystarReceiver* rcv, uint16_t s_prn) {
    // initialize selected satellite info
    rcv->p_prn = 0;
    rcv->p_snr = 0;
    memset(rcv->l6, 0, sizeof(rcv->l6));
    
  
    // check dictionary status
    bool dict_not_empty = false;

    for (int i = 193; i <= 211; i++) {
        if (rcv->dict_snr[i] != 0) {
            dict_not_empty = true;           
        }
    }
    
    if (rcv->last_gpst != rcv->gpst && dict_not_empty) {
        rcv->last_gpst = rcv->gpst;
        
        if (s_prn) {
            rcv->p_prn = s_prn;
        } else {
            // find the satellite with the highest SNR
            int max_snr = -1;
            uint16_t max_prn = 0;
            
            for (int prn = 193; prn <= 211; prn++) {
                if (rcv->dict_snr[prn] > max_snr) {
                    max_snr = rcv->dict_snr[prn];
                    max_prn = prn;
                }
            }
            
            if (max_snr > 0) {
                rcv->p_prn = max_prn;
            } else {
                rcv->p_prn = 0;
            }
        }
        
        // get the SNR and data of the selected satellite
        rcv->p_snr = rcv->dict_snr[rcv->p_prn];
        if (rcv->dict_snr[rcv->p_prn] != 0) {
            memcpy(rcv->l6, rcv->dict_data[rcv->p_prn], 252);          
        }        
   
        memset(rcv->dict_snr, 0, sizeof(rcv->dict_snr));
        memset(rcv->dict_data, 0, sizeof(rcv->dict_data));
    }
    
    // if there is no error, add the current data to the dictionary
    if (rcv->err[0] == '\0') {
        rcv->dict_snr[rcv->prn] = rcv->snr;
        memcpy(rcv->dict_data[rcv->prn], rcv->data, 252);      
    }     
}

int main(int argc, char* argv[]) {
    AllystarReceiver rcv;
    bool output_l6 = false;
    FILE* fp_raw = NULL;
    uint16_t s_prn = 0;
    
    // parse command line arguments
    for (int i = 1; i < argc; i++) {
        if (strcmp(argv[i], "-l") == 0) {
            output_l6 = true;
            fp_raw = stdout;
        }
        else if (strcmp(argv[i], "-p") == 0 && i + 1 < argc) {
            s_prn = atoi(argv[i + 1]);
            // check PRN range
            if ((s_prn < 193 || s_prn > 211) && s_prn != 0) {
                fprintf(stderr, "QZS L6 PRN is in range of 193-211 or 0\n");
                s_prn = 0;
            }
            i++;
        }
    }
    
    init_receiver(&rcv);
    
    while (read_data(&rcv)) {
        select_sat(&rcv, s_prn);
      
        // check if data is valid and fp_raw is valid
        if (rcv.l6[0] != 0 && fp_raw) {  // check if there is no error and fp_raw is valid
            fwrite(rcv.data, 1, 252, fp_raw); 
            fflush(fp_raw);
        }
    }
    
    // add signal processing
    signal(SIGPIPE, SIG_IGN);  // ignore SIGPIPE signal
    
    return 0;
}
