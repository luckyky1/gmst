clear;
clc;
global mycolor;
load('../color/mycolor_England_1.mat');
source1 = 'gistemp1200_GHCNv4_ERSSTv5.nc'; % 读取文件
time = double(ncread(source1, 'time')); % 查阅时间层数信息并转换为double类型
time_origin = datenum(1800, 1, 1); % 基准日期：1800-01-01
time_dates = time_origin + time; % 将time转换为实际日期
global time_months;
time_months = datestr(time_dates, 'mmm yyyy'); % 格式化日期为 月份和年份
ncdisp(source1); % 查阅nc文件信息
global boundary;
boundary = [-180 180 -90 90]; % 设置经纬度范围
lon = ncread(source1,'lon'); % 查阅经度信息
loncount = length(lon); % 查阅经度精度（有多少格点）
lat = ncread(source1,'lat'); % 查阅纬度信息
latcount = length(lat); % 查阅纬度精度（有多少格点）
time = ncread(source1,'time'); % 查阅时间层数信息
ticount = length(time); % 查阅时间层数
varname = 'tempanomaly'; % 根据ncdisp显示的变量输入绘图
lon_scope = find(lon >= boun dary(1) & lon <= boundary(2));
lat_scope = find(lat >= boundary(3) & lat <= boundary(4));
lon_number = length(lon_scope);
lat_number = length(lat_scope);
% 初始位置和读取范围
start = [lon_scope(1), lat_scope(1), 1]; % 初始位置
count = [lon_number, lat_number, ticount]; % 读取范围
stride1 = [1, 1, 1]; % 读取步长
sst0 = ncread(source1,varname,start,count,stride1); % 读取温度
for i = 2:1735
    sst2(:,:,i) = (sst0(:,:,i+1)-sst0(:,:,i-1))/2;
end
sst2(:,:,1)=NaN;
sst2(:,:,1736)=NaN;
SST_plot = flipud(imrotate(sst2(:,:,1), 90)); % 旋转矩阵
% 创建图形
figure1 = figure;
m_proj('Miller Cylindrical','lat',[boundary(3) boundary(4)],'lon',[boundary(1) boundary(2)]);
global lat_1;
global lon_1;
lat_1 = linspace(boundary(3),boundary(4),lat_number);
lon_1 = linspace(boundary(1),boundary(2),lon_number);
[plon, plat] = meshgrid(lon_1, lat_1);
colormap(mycolor)
% 将h_pcolor设为全局变量
global h_pcolor;
h_pcolor = m_pcolor(plon, plat, SST_plot);
set(h_pcolor, 'EdgeColor', 'none'); % 移除边框
m_coast('color',[0 0 0],'linewidth',1); % 绘制海岸线并填充陆地
m_grid('box','fancy'); % 添加边框
caxis([-4 4]);
title('dGMST/dt','fontsize',21); % 设置标题
%colormap jet; % 添加colorbar
h = colorbar('h');
set(get(h,'title'),'string','摄氏度℃');
% 将sst2设为全局变量
global sst2_global;
sst2_global = sst2;
% 添加滑动条
uicontrol('Style', 'text', 'String', '选择时间', 'Position', [65 9 100 20]);
time_slider = uicontrol('Style', 'slider', 'Min', 1, 'Max', ticount, 'Value', 1, ...
'Position', [150 12 300 20], 'SliderStep', [1/ticount, 12/ticount], 'Callback', @update_plot);

% for j = 1:length(indices_above_p99)
%     i = indices_above_p99(j);
%     png_save(i);
% end  
% disp('图像已保存到指定文件夹。');

% 启用数据光标并设置更新函数
dcm1 = datacursormode(figure1);
set(dcm1, 'UpdateFcn', @(src, event) data_cursor_function_map2(src, event, SST_plot, lon, lat));

function png_save(date)
save_folder = 'C:\大气物理\留存图片\'; % 修改为你的实际路径  
global sst2_global;
SST_plot = flipud(imrotate(sst2_global(:,:,date), 90)); % 旋转矩阵
global lat_1;
global lon_1;
global boundary;
global mycolor;
global time_months;
figure2 = figure;
m_proj('Miller Cylindrical','lat',[boundary(3) boundary(4)],'lon',[boundary(1) boundary(2)]);
[plon, plat] = meshgrid(lon_1, lat_1);
colormap(mycolor)
h_pcolor = m_pcolor(plon, plat, SST_plot);
set(h_pcolor, 'EdgeColor', 'none'); % 移除边框
m_coast('color',[0 0 0],'linewidth',1); % 绘制海岸线并填充陆地
m_grid('box','fancy'); % 添加边框
caxis([-4 4]);
month_t = time_months(date,:);
title(['dSST/dt at Time: ', month_t], 'fontsize', 21); % 更新标题
%colormap jet; % 添加colorbar
h = colorbar('h');
set(get(h,'title'),'string','摄氏度℃');
figHandle = gcf;  
filename = sprintf('%s %s.png',save_folder ,month_t);
saveas(figHandle, filename);  
end

% 更新图像的回调函数
function update_plot(source, ~)
global time_months;
global sst2_global; % 声明全局变量
global h_pcolor; % 声明全局变量
caxis([-4 4]);
t = round(get(source, 'Value')); % 获取滑动条的值
month_t = time_months(t,:);
sst_plot = flipud(imrotate(sst2_global(:,:,t), 90)); % 更新温度数据
set(h_pcolor, 'CData', sst_plot); % 更新绘制的内容
title(['dGMST/dt at Time: ', month_t], 'fontsize', 15); % 更新标题
drawnow; 
end

% 数据光标更新函数
function txt = data_cursor_function_map2(~, event_obj, SST_plot, lon, lat)
    pos = get(event_obj, 'Position'); % 获取光标位置
    x_value = pos(1);
    y_value = pos(2);

    % 将图形坐标转换为经纬度
    [lon_value, lat_value] = m_xy2ll(x_value, y_value); % 使用 m_xy2ll 函数

    % 找到最近的经纬度索引
    [~, lon_index] = min(abs(lon - lon_value));
    [~, lat_index] = min(abs(lat - lat_value));

    dsst = SST_plot(lat_index, lon_index);

    % 构建输出文本
    txt = {['经度: ', num2str(lon_value)], ...
           ['纬度: ', num2str(lat_value)], ...
           ['dsst： ', num2str(dsst)]}; % 显示具体的缺失值数量
end
%%
%%% --- START: 新增的合成分析部分 (V5 - 专业科研作图版) --- %%%
% 将此部分完整地替换掉您脚本中对应的部分

%% Part 2: 对已计算的变化率进行年度合成分析 (专业版)

fprintf('\n\n=============== 开始 Part 2: 年度变化率合成分析 (专业版) ===============\n');

% --- 【用户设置区】 ---
targetYear = 2006;
% -----------------------

% --- 1. 查找目标年份的时间索引 ---
[Y, ~, ~] = datevec(time_dates);
year_indices = find(Y == targetYear);
if isempty(year_indices)
    warning('在数据中没有找到 %d 年的任何月份，无法进行合成分析。', targetYear);
    return;
else
    fprintf('找到了 %d 个属于 %d 年的月份数据。\n', length(year_indices), targetYear);
end

% --- 2. 提取并平均该年份的变化率数据 ---
derivative_data_for_year = sst2_global(:,:,year_indices);
mean_derivative_for_year = mean(derivative_data_for_year, 3, 'omitnan');

% --- 3. 在一个新窗口中可视化合成结果 ---
figure('Name', sprintf('Scientific Composite Figure for %d', targetYear));
m_proj('Miller Cylindrical','lat', [boundary(3) boundary(4)], 'lon', [boundary(1) boundary(2)]);

% --- 【关键改动】使用更专业的绘图技巧 ---
[plon, plat] = meshgrid(lon_1, lat_1);
SST_plot_composite = flipud(imrotate(mean_derivative_for_year, 90));

% 第一步：绘制平滑的填色云图 (m_contourf)
contour_levels = 20; % 定义20个颜色填充等级
m_contourf(plon, plat, SST_plot_composite, contour_levels, 'LineStyle', 'none');
hold on;

% 第二步：在填色图上叠加黑色的正值等值线 (实线)
[C, h] = m_contour(plon, plat, SST_plot_composite, 'k-', 'LineWidth', 0.8);
clabel(C, h, 'LabelSpacing', 300, 'Color', 'k'); % 给等值线添加数值标签

% 第三步：在填色图上叠加白色的负值等值线 (虚线)
[C, h] = m_contour(plon, plat, SST_plot_composite, 'w--', 'LineWidth', 0.8);
clabel(C, h, 'LabelSpacing', 300, 'Color', 'w');

% 第四步：在数据之上绘制地理信息
m_coast('color', 'k', 'linewidth', 2); % 只画黑色的海岸线
m_grid('box','fancy');

% --- 绘图技巧改动结束 ---

% --- 【关键改动】使用 cmocean 色谱 ---
try
    colormap(cmocean('balance')); % 使用 'balance' 色谱，专为发散型数据设计
catch
    warning('cmocean 工具箱未找到，将使用默认颜色。请从网上下载并安装 cmocean。');
    colormap(mycolor); % 如果找不到 cmocean，则使用您原来的颜色
end

% 设置颜色轴和标题
min_val_comp = min(mean_derivative_for_year(:));
max_val_comp = max(mean_derivative_for_year(:));
max_abs_val = max(abs([min_val_comp, max_val_comp]));
caxis([-max_abs_val, max_abs_val]);
h_cbar_comp = colorbar('southoutside');
title(h_cbar_comp, '年平均温度变化率 (K/月)');
title(sprintf('%d年 温度变化率合成分析图', targetYear), 'fontsize', 16);

fprintf('=============== Part 2: 年度变化率合成分析完成 ===============\n');
fprintf('\n------------------ %d年 变化率合成图分析结果 ------------------\n', targetYear);
fprintf('本分析基于 %d 个有效月份的变化率计算结果。\n\n', length(year_indices));
fprintf('年平均变化率范围:\n');
fprintf('  -> 最小值: %.4f K/月\n', min_val_comp);
fprintf('  -> 最大值: %.4f K/月\n', max_val_comp);
fprintf('-----------------------------------------------------------------------\n');

%%% --- END: 新增的合成分析部分 --- %%%