int actuatorFwd = 19;
int actuatorRev = 18;
int actuatorPWM = 10;
int LED1PWM = 5;
int LED2PWM = 9;
int level=0;
int waitloop1=5;   // retract actuator
int waitloop2=5;  // extend actuator

void setup() {
  // put your setup code here, to run once:
pinMode(actuatorFwd,OUTPUT);
pinMode(actuatorRev,OUTPUT);
pinMode(actuatorPWM,OUTPUT);
pinMode(LED1PWM,OUTPUT);
pinMode(LED2PWM,OUTPUT);
}

void loop() {
  // put your main code here, to run repeatedly:
  digitalWrite(actuatorFwd,1);
  digitalWrite(actuatorRev,0);

  
  for (level=0; level < 255; level++) {
    analogWrite(actuatorPWM, level);
    analogWrite(LED1PWM, level);   
    delay(waitloop1);
  }
  for (level=255; level > 0; level--) {
    analogWrite(actuatorPWM, level);
    analogWrite(LED1PWM, level);   
    delay(waitloop1);
  }
   
  digitalWrite(actuatorFwd,0);
  digitalWrite(actuatorRev,1);
  
  for (; level < 255; level++) {
    analogWrite(actuatorPWM, level);
    analogWrite(LED2PWM, level);   
    delay(waitloop2);
  }
  for (; level > 0; level--) {
    analogWrite(actuatorPWM, level);
    analogWrite(LED2PWM, level);   
    delay(waitloop2);
  }
}
