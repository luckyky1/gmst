%% SLA 多年变化率的合成分析
%--------------------------------------------------------------------------
% 功能:
% 1. 对指定列表中的每一年[2006, 2012]，都计算其“年平均变化率”。
% 2. 将所有指定年份的“年平均变化率”再次求平均，得到最终的合成图。
% 3. 使用专业的科研绘图风格进行可视化。
%--------------------------------------------------------------------------

%% 1. 设置
clear; clc; close all;

% --- 【用户设置区】 ---
% 您想进行合成分析的年份列表
targetYears = [2006, 2012];
% --------------------

% 检查 cmocean 工具箱是否存在
try
    cmocean('balance');
    cmocean_is_available = true;
catch
    cmocean_is_available = false;
end

% --- 基本文件设置 ---
folderPath  = 'D:\SCIENCE\atmospheric_physic\daqi\qixiangzhishu\gmst\data\sea_level_grid';
latVarName  = 'latitude';
lonVarName  = 'longitude';
dataVarName = 'sla';

%% 2. 核心计算：嵌套循环与合成
fprintf('=============== 开始对指定年份列表进行SLA合成分析 ===============\n');
fprintf('目标年份: %s\n', num2str(targetYears));

% --- 预加载经纬度信息 ---
try
    first_file = dir(fullfile(folderPath, '*.nc'));
    first_path = fullfile(first_file(1).folder, first_file(1).name);
    lat = double(ncread(first_path, latVarName));
    lon = double(ncread(first_path, lonVarName));
catch
    error('无法读取经纬度信息，请检查文件夹路径和文件内容。');
end

% 初始化一个三维矩阵，用于存储每个目标年份的“年平均变化率”
composite_stack = NaN(size(lat,1), size(lon,1), length(targetYears));
years_processed_count = 0;

% 外层循环：遍历每一个目标年份
for i = 1:length(targetYears)
    currentYear = targetYears(i);
    fprintf('\n--- 正在处理年份: %d ---\n', currentYear);
    
    % --- 内层计算：获取当前年份的“年平均变化率” ---
    monthly_diffs = NaN(size(lat,1), size(lon,1), 12);
    months_in_year_count = 0;
    
    for month = 1:12
        try
            prevYear = currentYear - 1;
            nextYear = currentYear + 1;
            
            prevFilePattern = fullfile(folderPath, sprintf('*_%d%02d_*.nc', prevYear, month));
            prevFileInfo = dir(prevFilePattern);
            nextFilePattern = fullfile(folderPath, sprintf('*_%d%02d_*.nc', nextYear, month));
            nextFileInfo = dir(nextFilePattern);
            
            if isempty(prevFileInfo) || isempty(nextFileInfo)
                fprintf('  -> 跳过 %d 年 %02d 月：缺少前一年或后一年的数据文件。\n', currentYear, month);
                continue;
            end
            
            prevFilePath = fullfile(prevFileInfo(1).folder, prevFileInfo(1).name);
            nextFilePath = fullfile(nextFileInfo(1).folder, nextFileInfo(1).name);
            
            data_prev = double(ncread(prevFilePath, dataVarName, [1 1 1], [inf inf 1]))';
            data_next = double(ncread(nextFilePath, dataVarName, [1 1 1], [inf inf 1]))';
            
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
figure('Name', 'Multi-Year SLA Composite Analysis', 'Position', [100, 100, 1200, 800]);

% 手动创建坐标轴，预留底部空间
ax = axes('Position', [0.05, 0.15, 0.9, 0.8]);

% 使用Mapping Toolbox的axesm函数
axesm('MapProjection', 'robinson', 'Origin', [0 180 0], ...
      'Frame', 'on', 'FEdgeColor', 'k', ...
      'Grid', 'off', ...
      'MLineLocation', 30, 'PLineLocation', 30, ...
      'MeridianLabel', 'on', 'ParallelLabel', 'on', ...
      'FontSize', 12);

geoshow('landareas.shp', 'FaceColor', [0.6 0.6 0.6], 'EdgeColor', 'k');
hold on;

pcolorm(lat, lon, final_composite_map);

h_cbar = colorbar('southoutside');
cbar_pos = get(h_cbar, 'Position');
cbar_pos(2) = cbar_pos(2) - 0.04;
set(h_cbar, 'Position', cbar_pos);

if cmocean_is_available
    colormap(ax, cmocean('balance'));
else
    colors = [0 0 1; 1 1 1; 1 0 0];
    positions = [0, 0.5, 1];
    my_bwr = interp1(positions, colors, linspace(0, 1, 256));
    colormap(ax, my_bwr);
end

min_val = min(final_composite_map(:));
max_val = max(final_composite_map(:));
max_abs_val = 0.08;
caxis([-max_abs_val, max_abs_val]);
num_ticks = 11;
ticks = linspace(-max_abs_val, max_abs_val, num_ticks);
tickLabels = cell(size(ticks));
for k = 1:length(ticks)
    tickLabels{k} = sprintf('%.4f', ticks(k));
end
set(h_cbar, 'Ticks', ticks, 'TickLabels', tickLabels, 'FontSize', 14);
title(h_cbar, '合成年平均SLA变化率 (米/年)', 'FontSize', 16);
title_str = sprintf('特定年份合成SLA变化率 (%d 个年份平均)', years_processed_count);
h_title = title(title_str, 'fontsize', 18, 'FontWeight', 'bold');
% 获取标题当前位置
title_pos = get(h_title, 'Position');
% 将标题的Y坐标值增加5%，使其上移 (您可以调整 1.05 这个值)
title_pos(2) = title_pos(2) * 1.05; 
set(h_title, 'Position', title_pos);
% ----------------------------------------------------

%% 4. 在命令行输出量化结果
fprintf('\n------------------ 多年SLA合成分析结果 ------------------\n');
fprintf('本分析基于以下 %d 个年份的年平均变化率合成得到:\n', years_processed_count);
disp(targetYears);
fprintf('\n最终合成场的变化率范围:\n');
fprintf('  -> 最小值: %.4f 米/年\n', min_val);
fprintf('  -> 最大值: %.4f 米/年\n', max_val);
fprintf('-----------------------------------------------------------\n');