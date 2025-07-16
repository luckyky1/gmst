clear;clc;
load("ONI.txt");
ONI1=ONI(1:73,2:13);
ONI2=ONI(2:74,2:13);
oni1 = ONI1(:,11)+ONI1(:,12);
oni2 = ONI2(:,1);
oni = ( oni1 + oni2 ) / 3;
pn = polyfit(1:73,oni,1);
y = pn(1)*(1:73) + pn(2);

gmst = csvread("GMSTyear.csv");
gmst = gmst(72:144);
pm = polyfit(1:73,gmst,1);
z = pm(1)*(1:73) + pm(2);

figure;
subplot(2,1,1);
hold on;
set(gca,'Linewidth',1.7);
plot((1:73)+1949,oni','Color',[1 0.54 0],'LineWidth', 2);
plot((1:73)+1949,y,'Color',[0.043 0.1961 0.5373],'LineWidth', 2);
legend('ONI','ONI\_profit');
subplot(2,1,2);
hold on;
set(gca,'Linewidth',1.7);
plot((1:73)+1949,gmst,'Color',[1 0.54 0],'LineWidth', 2);
plot((1:73)+1949,z,'Color',[0.043 0.1961 0.5373],'LineWidth', 2);
legend('GMST','GMST\_profit',Location='southeast');

a = (gmst - z');
a = a(2:73);
b = 10 * a;
oni = oni(1:72);
corr(a,oni)
figure;
hold on;
set(gca,'Linewidth',1.7);
plot((1:72)+1950,oni','Color',[1 0.54 0],'LineWidth', 2);
plot((1:72)+1950,a,'Color',[0.043 0.1961 0.5373],'LineWidth', 2);
plot((1:72)+1950,b,'Color',[184,100,211]/255,'LineWidth', 2);
legend('ONI','\epsilon_{GMST}','10\times \epsilon_{GMST}');

pn1 = polyfit(oni,a,1);
ay = pn1(1)*oni + pn1(2);
figure;
hold on;
set(gca,'Linewidth',1.7);
plot((1:72)+1950,a,'Color',[0.043 0.1961 0.5373],'LineWidth', 2);
plot((1:72)+1950,ay,'Color',[1 0.54 0],'LineWidth', 2);
legend('GMST','Predict\_GMST');

u = a - ay;
figure;
hold on;
set(gca,'Linewidth',1.7);
plot((1:72)+1950,u,'Color',[0.043 0.1961 0.5373],'LineWidth', 2);
