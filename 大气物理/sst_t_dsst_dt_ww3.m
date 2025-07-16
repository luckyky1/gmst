clear;
clc;
load('Global_topog_area_lat_rec.mat');
area1 = (area(1:2:179) + area(2:2:180)) / 2; % 取平均
area2 = area1 / sum(area1) * 90;
area3 = repmat(area2, 180, 1);
source1 = 'gistemp1200_GHCNv4_ERSSTv5.nc'; % 读取文件
ncdisp(source1); % 查阅nc文件信息
boundary = [-180 180 -90 90]; % 设置经纬度范围
lon = ncread(source1, 'lon'); % 查阅经度信息
lat = ncread(source1, 'lat'); % 查阅纬度信息
time = double(ncread(source1, 'time')); % 查阅时间层数信息并转换为double类型
time_origin = datenum(1800, 1, 1); % 基准日期：1800-01-01
time_dates = time_origin + time; % 将time转换为实际日期
varname = 'tempanomaly'; % 温度异常变量名
lon_scope = find(lon >= boundary(1) & lon <= boundary(2));
lat_scope = find(lat >= boundary(3) & lat <= boundary(4));
lon_number = length(lon_scope);
lat_number = length(lat_scope);

% 初始位置和读取范围
start = [lon_scope(1), lat_scope(1), 1]; % 初始位置
count = [lon_number, lat_number, length(time)]; % 读取范围
stride1 = [1, 1, 1]; % 读取步长
sst1 = ncread(source1, varname, start, count, stride1); % 读取温度数据
sst2 = sst1; % 转换为摄氏度并应用缩放因子
sst3 = sst2 .* area2;

% 计算每个时间点的平均温度
mean_temp_time_series = squeeze(mean(sst3, [1, 2], 'omitnan')); % 对lon和lat求平均

% 三个月滑动平均数据
y = NaN(floor(length(mean_temp_time_series) / 3), 1); % 初始化
time_dates_trimonthly = NaN(length(y), 1); % 三个月时间点
for i = 1:3:length(mean_temp_time_series) - 2
    y((i + 2) / 3) = mean(mean_temp_time_series(i:i+2), 'omitnan'); % 每三个月平均
    time_dates_trimonthly((i + 2) / 3) = mean(time_dates(i:i+2)); % 三个月的中间时间
end

% 消去季节影响
mo = NaN(4, 1); % 三个月为一组，总共4组
for i = 1:4
    stid = 440 + i; % 对应三个月平均后的时间点起点
    sgt = reshape(y(stid:4:stid + 4 * 29), [30, 1]); % 到2020年
    mo(i) = mean(sgt);
end

y_deseasoned = NaN(size(y));
for i = 1:length(y)
    season_idx = 1 + mod(i - 1, 4); % 三个月一组
    y_deseasoned(i) = y(i) - mo(season_idx);
end

% 计算 d(GMST)/dt）
dydt = NaN(size(y_deseasoned)); % 初始化
for i = 2:length(y_deseasoned) - 1
    dydt(i) = (y_deseasoned(i+1) - y_deseasoned(i-1)) / 2; % 计算局部斜率
end

% 计算斜率的百分位数
percentile_90w = prctile(dydt, 90);
percentile_95w = prctile(dydt, 95);
percentile_99w = prctile(dydt, 98);
line=0.2;
% 找到快速上升期
indices_above_p99w = find(dydt > percentile_99w);
indices_above_p99_validw = indices_above_p99w(indices_above_p99w < length(y_deseasoned) - 1);
figure
histogram(dydt)

s(1) = 0;
for i = 2:length(y)
    s(i) = s(i-1)+ismember(i,indices_above_p99_validw).*(y(i)-y(i-1));
end
s = s';
ys = y-s;

% 绘制原始温度异常时间序列
figure3 = figure;
hold on;
plot(time_dates_trimonthly, y, 'LineWidth', 1.5); % 三个月平均时间序列
plot(time_dates_trimonthly, ys, 'LineWidth', 1.5); % 三个月平均时间序列
scatter(time_dates_trimonthly(indices_above_p99_validw + 1), y(indices_above_p99_validw + 1), 'ro', 'filled');
datetick('x', 'mmm yyyy');
xlabel('时间', 'fontsize', 12);
ylabel('平均GMST (°C)', 'fontsize', 12);
title('全球温度异常时间序列（三个月平均）', 'fontsize', 15);
grid on;
dcm3 = datacursormode(figure3);
set(dcm3, 'UpdateFcn', @myupdatefcn);

% 绘制 d(GMST)/dt 时间序列
figure4 = figure;
hold on;
plot(time_dates_trimonthly, dydt, 'b', 'LineWidth', 1.5); % 三个月时间点
plot(time_dates_trimonthly, percentile_90w * ones(size(dydt)), '--k');
plot(time_dates_trimonthly, percentile_95w * ones(size(dydt)), '--m');
plot(time_dates_trimonthly, percentile_99w * ones(size(dydt)), '--r');
scatter(time_dates_trimonthly(indices_above_p99_validw), dydt(indices_above_p99_validw), 'ro', 'filled');
datetick('x', 'mmm yyyy');
xlabel('时间', 'fontsize', 12);
ylabel('d(GMST)/dt (°C/三月)', 'fontsize', 12);
title('全球温度变化率 (d(GMST)/dt) 时间序列（三个月平均）', 'fontsize', 15);
grid on;
dcm4 = datacursormode(figure4); 
set(dcm4, 'UpdateFcn', @myupdatefcn);

% 数据光标更新函数
function txt = myupdatefcn(~, event_obj)  
    pos = get(event_obj, 'Position');  
    x_time = pos(1); % 提取x轴时间
    y_value = pos(2); % 提取y轴值
    % 计算三个月的时间范围
    start_month = datestr(x_time - 45, 'mmm yyyy');
    middle_month = datestr(x_time, 'mmm yyyy');
    end_month = datestr(x_time + 45, 'mmm yyyy');
    txt = {['时间: ', start_month, ', ', middle_month, ', ', end_month, ' 平均'], ...
           ['值: ', num2str(y_value)]};  
end
