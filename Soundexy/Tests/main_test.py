from scipy.io import wavfile

wave_obj = wavfile.read("C:\\Users\\smith\\Downloads\\Sounddogs_Order\\Humvee, Onb,55 MPH,"
                        "Start Idle Revs,Drive Fast,Uphill Accelerate H,6003_966817.wav")
print(wave_obj[0])
