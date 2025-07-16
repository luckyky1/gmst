clear;
clc;
load('Global_topog_area_lat_rec.mat');
area1 = (area(1:2:179)+area(2:2:180))/2;%取平均
area2 = area1 / sum(area1) * 90;
area3 = repmat(area2,180,1);
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
% 消去季节影响
for i = 1:12
    stid = 1320 + i; % 从1991年开始(1320)
    sgt = reshape(mean_temp_time_series(stid:12:stid + 12*29), [30,1]); % 到2020年
    mo(i) = mean(sgt);
end
for i = 1:1736
    y(i) = mean_temp_time_series(i) - mo(12 + mod(-i,-12));
end
%res = kron(ones(1,143),residualCopy);%【residualCopy从experiment中运行并复制】
%res = res(1,1:1736);
%y = y+res;

% 计算d(GMST)/dt）
dydt = NaN(size(y)); % 初始化d0
for i = 2:length(y)-1
    dydt(i) = (y(i+1) - y(i-1)) / 2; % 计算局部斜率
end
figure;
histogram(dydt)

% 计算斜率的百分位数，用于识别快速上升的时期
percentile_90w = prctile(dydt, 90);
percentile_95w = prctile(dydt, 95);
percentile_99w = prctile(dydt, 99);

% 找到快速上升期（超过99百分位数的点）
line = 0.12
indices_above_p99w = find(dydt > percentile_99w);

% 修正索引，避免超出范围
indices_above_p99_validw = indices_above_p99w(indices_above_p99w < length(time_dates) - 1); % 确保索引在范围内
%%

s(1) = 0
for i = 2:length(y)
    s(i) = s(i-1)+ismember(i,indices_above_p99_validw).*(y(i)-y(i-1));
end
ys = y-s;

%绘制未经LOESS平滑的dSST\dt时间序列
figure4 = figure('Position',[100 100 1200 500]);
hold on;
plot(time_dates(2:end), dydt(2:end), 'Color',[0 0.45 0.74], 'LineWidth', 1.8); % 绘制平滑后的斜率曲线
plot(time_dates(2:end), percentile_90w*ones(size(dydt(2:end))), '--','Color',[0.5 0.5 0.5]);
plot(time_dates(2:end), percentile_95w*ones(size(dydt(2:end))), '--m');
plot(time_dates(2:end), percentile_99w*ones(size(dydt(2:end))), '--r');
scatter(time_dates(indices_above_p99_validw), dydt(indices_above_p99_validw), 'MarkerEdgeColor',[0.85 0.12 0],'MarkerFaceColor',[0.85 0.12 0], 'LineWidth',0.8); % 修正索引
datetick('x', 'mmm yyyy');
set(gca, 'FontSize',12, 'FontName', 'Microsoft YaHei','LineWidth',1.2);
xlabel('时间', 'fontsize', 14, 'FontName','Microsoft YaHei');
ylabel('d(GMST)/dt (°C/月)', 'fontsize', 14, 'FontName','Microsoft YaHei');
title('全球温度变化率 (d(GMST)/dt) 时间序列', 'fontsize', 16, 'FontWeight','bold', 'FontName','Microsoft YaHei');
grid on;
box on;

%绘制原始时间序列
figure3 = figure('Position',[100 100 1200 500]);
hold on;
plot(time_dates, y, 'Color',[1 0.54 0], 'LineWidth', 2.2); % 绘制平滑后的温度异常时间序列
plot(time_dates,ys, 'Color',[0.043 0.1961 0.5373], 'LineWidth', 2);
scatter(time_dates(indices_above_p99_validw + 1), y(indices_above_p99_validw + 1), 'MarkerEdgeColor',[0.59294 0.59294 0.59294], 'MarkerFaceColor',[0.59294 0.59294 0.59294], 'LineWidth',0.8);
datetick('x', 'mmm yyyy');
set(gca, 'FontSize',12, 'FontName',' Macrosoft YaHei', 'LineWidth',1.2);
xlabel('时间', 'fontsize', 14, 'FontName','Microsoft YaHei');
ylabel('平均GMST (°C)', 'fontsize', 14, 'FontName','Microsoft YaHei');
title('全球温度异常时间序列', 'fontsize', 16, 'FontWeight','bold', 'FontName','Microsoft YaHei');
legend({'原始序列','去除急速上升影响后序列','急速上升点'}, 'FontSize',12, 'Location','northwest');
grid on;
box on;
% dcm1 = datacursormode(figure1);  
% set(dcm1, 'UpdateFcn', @myupdatefcn);
% dcm2 = datacursormode(figure2); 
% set(dcm2, 'UpdateFcn', @myupdatefcn); 
dcm3 = datacursormode(figure3); 
set(dcm3, 'UpdateFcn', @myupdatefcn); 
dcm4 = datacursormode(figure4); 
set(dcm4, 'UpdateFcn', @myupdatefcn); 
% 定义数据光标更新函数，必须放在文件末尾
function txt = myupdatefcn(~, event_obj)  
    pos = get(event_obj, 'Position');  
    target = get(event_obj, 'Target'); 
    xdata_full = get(target, 'XData'); 
    ydata_full = get(target, 'YData'); 
    xdata_index = find(abs(xdata_full - pos(1, 1)) == min(abs(xdata_full - pos(1, 1)))); 
    xdata = xdata_full(xdata_index); 
    ydata = ydata_full(xdata_index); 
    datestr_x = datestr(xdata, 'yyyy-mm-dd');   
    txt = {['X: ', datestr_x], ['Y: ', num2str(ydata)]};  
end