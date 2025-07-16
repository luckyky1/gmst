% 清除变量和命令行窗口
clear;
clc;

% 加载数据
load('Global_topog_area_lat_rec.mat');
area1 = (area(1:2:179) + area(2:2:180)) / 2; % 取平均
area2 = area1 / sum(area1) * 90;
area3 = repmat(area2, 180, 1);
source1 = 'gistemp1200_GHCNv4_ERSSTv5.nc'; % 读取文件
boundary = [-180 180 -90 90]; % 设置经纬度范围

% 读取数据
lon = ncread(source1, 'lon'); % 经度信息
lat = ncread(source1, 'lat'); % 纬度信息
time = double(ncread(source1, 'time')); % 时间层数信息
time_origin = datenum(1800, 1, 1); % 基准日期
time_dates = time_origin + time; % 转换为实际日期
varname = 'tempanomaly'; % 温度异常变量名

% 初始位置和读取范围
lon_scope = find(lon >= boundary(1) & lon <= boundary(2));
lat_scope = find(lat >= boundary(3) & lat <= boundary(4));
start = [lon_scope(1), lat_scope(1), 1]; % 初始位置
count = [length(lon_scope), length(lat_scope), length(time)]; % 读取范围
sst1 = ncread(source1, varname, start, count); % 读取温度数据
sst2 = sst1 .* area2; % 应用缩放因子

% 计算每个月的全球平均温度
mean_temp_time_series = squeeze(mean(sst2, [1, 2], 'omitnan'));

% 计算年平均值
num_years = floor(length(mean_temp_time_series) / 12); % 完整年份数
y_yearly = zeros(1, num_years); % 初始化年平均值
time_yearly = zeros(1, num_years); % 初始化年份

for i = 1:num_years
    start_idx = (i - 1) * 12 + 1;
    end_idx = start_idx + 11;
    y_yearly(i) = mean(mean_temp_time_series(start_idx:end_idx), 'omitnan'); 
    time_yearly(i) = time_dates(start_idx); % 年份
end

dydt(1) = y_yearly(2)-y_yearly(1);
for i =2:143
    dydt(i) = (y_yearly(i+1)-y_yearly(i-1))/2;
end
histogram(dydt);
indices = find(dydt>0.13);

s(1) = 0
for i = 2:length(y_yearly)
    s(i) = s(i-1)+ismember(i,indices).*(y_yearly(i)-y_yearly(i-1));
end
ys = y_yearly-s;

% 绘制年平均时间序列
figure;
hold on;
plot(time_yearly, y_yearly, 'b-', 'LineWidth', 1.5);
%plot(time_yearly, ys,  'LineWidth', 1.5);
scatter(time_yearly(indices),y_yearly(indices),'ro', 'filled');
xlabel('年份', 'fontsize', 12);
ylabel('全球平均温度异常 (°C)', 'fontsize', 12);
title('全球年平均温度异常时间序列', 'fontsize', 15);
grid on;

% 设置横轴为年份
xticks(time_yearly(1:5:end)); % 每隔5年显示一个刻度
xticklabels(arrayfun(@(x) datestr(x, 'yyyy'), time_yearly(1:5:end), 'UniformOutput', false));

% 数据光标模式设置
dcm = datacursormode(gcf);
set(dcm, 'UpdateFcn', @myupdatefcn);

% 自定义数据光标更新函数
function txt = myupdatefcn(~, event_obj)
    pos = get(event_obj, 'Position');
    x_time = datestr(pos(1), 'yyyy年'); % 年份
    y_value = pos(2); % 温度值
    txt = {['年份: ', x_time], ['值: ', num2str(y_value, '%.4f'), ' °C']};
end
