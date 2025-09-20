%% OHC 多年变化率的合成分析
%--------------------------------------------------------------------------
% 功能:
% 1. 加入了手动微调Colorbar垂直位置的功能。
% 2. 对指定OHC年份列表进行“年平均变化率”合成分析。
% 3. 使用专业的科研绘图风格进行可视化。
%--------------------------------------------------------------------------

%% 1. 设置
clear; clc; close all;

% --- 【用户设置区】 ---
% 您想进行合成分析的OHC年份列表
targetYears = [1958, 1962, 2003, 2017];
% --------------------

% 检查 cmocean 工具箱是否存在
try
    cmocean('balance');
    cmocean_is_available = true;
catch
    cmocean_is_available = false;
end

% --- 基本文件设置，指向OHC数据 ---
basePath    = 'D:\SCIENCE\atmospheric_physic\daqi\qixiangzhishu\gmst\data\ohc\dataall';
latVarName  = 'lat';
lonVarName  = 'lon';
dataVarName = 'OHC2000';
filePrefix  = 'OHC_IAP_0_6000m'; % OHC文件名前缀
dataType    = 'OHC'; % 用于构建文件夹名称
% --- 设置结束 ---

%% 2. 核心计算：嵌套循环与合成
fprintf('=============== 开始对指定年份列表进行OHC合成分析 ===============\n');
fprintf('目标年份: %s\n', num2str(targetYears));

% --- 预加载经纬度信息 ---
try
    first_year_folder = fullfile(basePath, [dataType, num2str(targetYears(1))]);
    first_file_info = dir(fullfile(first_year_folder, '*.nc'));
    first_path = fullfile(first_file_info(1).folder, first_file_info(1).name);
    lat = double(ncread(first_path, latVarName));
    lon = double(ncread(first_path, lonVarName));
catch
    error('无法读取经纬度信息，请检查文件夹路径和文件内容。');
end

% 初始化一个三维矩阵，用于存储每个目标年份的“年平均变化率”
composite_stack = NaN(length(lon), length(lat), length(targetYears));
years_processed_count = 0;

% 外层循环：遍历每一个目标年份
for i = 1:length(targetYears)
    currentYear = targetYears(i);
    fprintf('\n--- 正在处理年份: %d ---\n', currentYear);

    % --- 内层计算：获取当前年份的“年平均变化率” ---
    monthly_diffs = NaN(length(lon), length(lat), 12);
    months_in_year_count = 0;

    for month = 1:12
        try
            prevYear = currentYear - 1;
            nextYear = currentYear + 1;
            
            prevFileName = sprintf('%s_year_%d_month_%02d.nc', filePrefix, prevYear, month);
            nextFileName = sprintf('%s_year_%d_month_%02d.nc', filePrefix, nextYear, month);
            
            prevFilePath = fullfile(basePath, [dataType, num2str(prevYear)], prevFileName);
            nextFilePath = fullfile(basePath, [dataType, num2str(nextYear)], nextFileName);
            
            if ~exist(prevFilePath, 'file') || ~exist(nextFilePath, 'file')
                fprintf('  -> 跳过 %d 年 %02d 月：缺少前一年或后一年的数据文件。\n', currentYear, month);
                continue;
            end
            
            data_prev = double(ncread(prevFilePath, dataVarName));
            data_next = double(ncread(nextFilePath, dataVarName));
            
            data_prev(data_prev > 1e20) = NaN;
            data_next(data_next > 1e20) = NaN;
            
            monthly_diffs(:,:,month) = (data_prev - data_next) / 2;
            months_in_year_count = months_in_year_count + 1;
        catch ME
             fprintf('  -> 处理 %d 年 %02d 月时发生错误: %s\n', currentYear, month, ME.message);
        end
    end

    if months_in_year_count > 0
        annual_mean_rate = mean(monthly_diffs, 3, 'omitnan');
        composite_stack(:,:,i) = annual_mean_rate;
        years_processed_count = years_processed_count + 1;
        fprintf('--- 年份 %d 处理完成，共计算了 %d 个月。 ---\n', currentYear, months_in_year_count);
    else
        fprintf('--- 年份 %d 处理失败，没有任何有效月份。 ---\n', currentYear);
    end
end

if years_processed_count == 0
    error('未能成功处理任何指定年份，分析终止。');
end

% --- 最终合成：对所有年份的“年平均变化率”求平均 ---
final_composite_map = mean(composite_stack, 3, 'omitnan');
fprintf('\n=============== 所有年份合成完毕！ ===============\n');

%% 3. 结果可视化
figure('Name', 'Multi-Year OHC Composite Analysis', 'Position', [100, 100, 1200, 800]);
ax = axes('Position', [0.05, 0.15, 0.9, 0.75]);
axesm('MapProjection', 'robinson', 'Origin', [0 180 0], ...
      'Frame', 'on', 'FEdgeColor', 'k', ...
      'Grid', 'off', ...
      'MLineLocation', 60, 'PLineLocation', 30, ...
      'MeridianLabel', 'on', 'ParallelLabel', 'on', ...
      'FontSize', 12);
geoshow('landareas.shp', 'FaceColor', [0.6 0.6 0.6], 'EdgeColor', 'k');
hold on;

pcolorm(lat, lon, final_composite_map');

% --- 【关键修正】使用更简单、更稳健的方式创建和标注Colorbar ---

% 1. 创建颜色条
h_cbar = colorbar('southoutside');

% 2. 手动微调Colorbar与主图的垂直位置
cbar_pos = get(h_cbar, 'Position');
cbar_pos(2) = cbar_pos(2) - 0.1;
set(h_cbar, 'Position', cbar_pos);

% 3. 设置刻度和标签（保持不变）
min_val = min(final_composite_map(:));
max_val = max(final_composite_map(:));
max_abs_val = 0.2*max(abs([min_val, max_val]));
caxis([-max_abs_val, max_abs_val]);
num_ticks = 11;
ticks = linspace(-max_abs_val, max_abs_val, num_ticks);
tickLabels = cell(size(ticks));
for k = 1:length(ticks)
    tickLabels{k} = sprintf('%.2e', ticks(k));
end
set(h_cbar, 'Ticks', ticks, 'TickLabels', tickLabels, 'FontSize', 14);

% 4. 【新】使用 ylabel 命令为Colorbar添加标题
ylabel(h_cbar, '合成年平均OHC变化率 (J·m^{-2}·yr^{-1})', 'FontSize', 16);

% --- 修正结束 ---


if cmocean_is_available
    colormap(ax, cmocean('balance'));
else
    colors = [0 0 1; 1 1 1; 1 0 0];
    positions = [0, 0.5, 1];
    my_bwr = interp1(positions, colors, linspace(0, 1, 256));
    colormap(ax, my_bwr);
end

% --- 主标题的调整代码保持不变 ---
title_str = sprintf('特定年份合成OHC变化率 (%d 个年份平均)', years_processed_count);
h_title = title(title_str, 'fontsize', 18, 'FontWeight', 'bold');
title_pos = get(h_title, 'Position');
title_pos(2) = title_pos(2) * 1.05; 
set(h_title, 'Position', title_pos);
% ---------------------------------
%% 4. 在命令行输出量化结果
fprintf('\n------------------ 多年OHC合成分析结果 ------------------\n');
fprintf('本分析基于以下 %d 个年份的年平均变化率合成得到:\n', years_processed_count);
disp(targetYears);
fprintf('\n最终合成场的变化率范围:\n');
fprintf('  -> 最小值: %.2e J·m^{-2}·yr^{-1}\n', min_val);
fprintf('  -> 最大值: %.2e J·m^{-2}·yr^{-1}\n', max_val);
fprintf('-----------------------------------------------------------\n');