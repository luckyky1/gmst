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
time_months = datestr(time_dates, 'mmm yyyy'); % 格式化日期为 月份和年份
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

% 四个月滑动平均数据
y4 = NaN(floor(length(mean_temp_time_series) / 4), 1); % 初始化
time_dates_quarterly = NaN(length(y4), 1); % 四个月时间点
for i = 1:4:length(mean_temp_time_series) - 3
    y4((i + 3) / 4) = mean(mean_temp_time_series(i:i+3), 'omitnan'); % 每四个月平均
    time_dates_quarterly((i + 3) / 4) = mean(time_dates(i:i+3)); % 四个月的中间时间
end

% 消去季节影响
mo = NaN(4, 1); % 四个月为一组，总共4组
for i = 1:4
    stid = i; % 每四个月一组
    sgt = y4(stid:4:end); % 每四个月数据提取
    mo(i) = mean(sgt); % 计算季节性平均
end
y4_deseasoned = y4;
for i = 1:length(y4)
    season_idx = 1 + mod(i - 1, 4); % 四个月一组
    y4_deseasoned(i) = y4(i) - mo(season_idx);
end

%计算 d(GMST)/dt）
dydt = NaN(size(y4_deseasoned)); % 初始化
for i = 2:length(y4_deseasoned) - 1
    dydt(i) = (y4_deseasoned(i+1) - y4_deseasoned(i-1)) / 2; % 计算局部斜率
end
% %初始化异常点累积贡献和去异常后的数据
% s(1) = 0; % 异常点累积贡献初始值
% ys = y;   % 去异常后的数据初始化
% 
% % 计算异常点的累积贡献和去异常后的数据
% for i = 2:length(y)
%     s(i) = s(i-1) + ismember(i, indices_above_p99_validw) * (y(i) - y(i-1));
%     ys(i) = y(i) - ismember(i, indices_above_p99_validw) * (y(i) - y(i-1));
% end
figure;
histogram(dydt);
% 计算斜率的百分位数
percentile_90w4 = prctile(dydt, 90);
percentile_95w4 = prctile(dydt, 95);
percentile_99w4 = prctile(dydt, 97);
line=0.15;
% 找到快速上升期
indices_above_p99w4 = find(dydt >percentile_99w4);
indices_above_p99_validw4 = indices_above_p99w4(indices_above_p99w4 < length(y4_deseasoned) - 1);

s(1) = 0
for i = 2:length(y)
    s(i) = s(i-1)+ismember(i,indices_above_p99_validw).*(y(i)-y(i-1));
end
s=s';
ys = y-s;

% 绘制原始温度异常时间序列
figure3 = figure;
hold on;
plot(time_dates_quarterly, y4, 'LineWidth', 1.5); % 四个月平均时间序列
scatter(time_dates_quarterly(indices_above_p99_validw4 + 1), y4(indices_above_p99_validw4 + 1), 'ro', 'filled');
datetick('x', 'mmm yyyy');
xlabel('时间', 'fontsize', 12);
ylabel('平均GMST (°C)', 'fontsize', 12);
title('全球温度异常时间序列（四个月平均）', 'fontsize', 15);
grid on;
dcm3 = datacursormode(figure3);
set(dcm3, 'UpdateFcn', @myupdatefcn);

% 绘制 d(GMST)/dt 时间序列
figure4 = figure;
hold on;
plot(time_dates_quarterly, dydt, 'b', 'LineWidth', 1.5); % 四个月时间点
plot(time_dates_quarterly, percentile_90w4 * ones(size(dydt)), '--k');
plot(time_dates_quarterly, percentile_95w4 * ones(size(dydt)), '--m');
plot(time_dates_quarterly, percentile_99w4 * ones(size(dydt)), '--r');
scatter(time_dates_quarterly(indices_above_p99_validw4), dydt(indices_above_p99_validw4), 'ro', 'filled');
datetick('x', 'mmm yyyy');
xlabel('时间', 'fontsize', 12);
ylabel('d(GMST)/dt (°C/四月)', 'fontsize', 12);
title('全球温度变化率 (d(GMST)/dt) 时间序列（四个月平均）', 'fontsize', 15);
grid on;
dcm4 = datacursormode(figure4);
set(dcm4, 'UpdateFcn', @myupdatefcn);

% 数据光标更新函数
function txt = myupdatefcn(~, event_obj)
    pos = get(event_obj, 'Position');
    x_time = pos(1);
    y_value = pos(2);
    
    % 计算四个月的时间范围
    start_month = datestr(x_time - 60, 'yyyy.mm');
    middle_month_1 = datestr(x_time - 30, 'yyyy.mm');
    middle_month_2 = datestr(x_time, 'yyyy.mm');
    end_month = datestr(x_time + 30, 'yyyy.mm');
    
    % 返回格式化的文本，显示四个月的日期范围
    txt = {['时间: ', start_month, '，', middle_month_1, '，', middle_month_2, '，', end_month], ...
           ['值: ', num2str(y_value)]};
end
