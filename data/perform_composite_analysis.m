%% OHC 多年变化率的合成分析 (单一文件最终版)
%--------------------------------------------------------------------------
% 功能:
% 1. 将所有分析步骤整合到一个脚本中，无需额外函数文件。
% 2. 对指定的OHC年份列表进行“年平均变化率”合成分析。
% 3. 使用 M_Map 工具箱进行稳健、专业的地理绘图。
% 4. 包含详细的诊断信息，便于排查问题。
%--------------------------------------------------------------------------

%% 1. 设置
clear; clc; close all;

% --- 【用户设置区】 ---
% 1. 定义要分析的年份
targetYears = [1958, 1962, 2003, 2017];

% 2. 定义数据类型和文件名前缀
dataType    = 'OHC';
filePrefix  = 'OHC_IAP_0_6000m';

% 3. 定义数据文件夹的根路径
basePath    = 'D:\SCIENCE\atmospheric_physic\daqi\qixiangzhishu\gmst\data\ohc\dataall';

% 4. 【必须确认】定义NC文件内部的变量名
latVarName  = 'lat';
lonVarName  = 'lon';
dataVarName = 'OHC2000';
% --- 设置结束 ---


%% 2. 初始化和预加载
fprintf('\n\n================================================================\n');
fprintf('开始为 [%s] 数据类型进行多年合成分析...\n', dataType);
fprintf('目标年份: %s\n', num2str(targetYears));

% 检查 cmocean 工具箱
try
    cmocean('balance');
    cmocean_is_available = true;
catch
    cmocean_is_available = false;
    fprintf('提示: cmocean工具箱未找到，将使用默认颜色图。\n');
end

% 预加载坐标数据
try
    first_year_folder = fullfile(basePath, [dataType, num2str(targetYears(1))]);
    first_file_info = dir(fullfile(first_year_folder, '*.nc'));
    if isempty(first_file_info)
        error('文件夹 "%s" 中找不到任何.nc文件。', first_year_folder);
    end
    first_file_path = fullfile(first_file_info(1).folder, first_file_info(1).name);
    lat = double(ncread(first_file_path, latVarName));
    lon = double(ncread(first_file_path, lonVarName));
catch ME
    error('无法读取经纬度信息，请检查文件夹结构或经纬度变量名 ("%s", "%s") 是否正确。\n错误详情: %s', latVarName, lonVarName, ME.message);
end

%% 3. 核心计算：嵌套循环与合成
composite_stack = NaN(length(lon), length(lat), length(targetYears));
years_processed_count = 0;

for i = 1:length(targetYears)
    currentYear = targetYears(i);
    fprintf('\n--- 正在处理年份: %d ---\n', currentYear);
    
    monthly_diffs = NaN(length(lon), length(lat), 12);
    months_in_year_count = 0;
    
    for month = 1:12
        fprintf('  -- 正在处理 %d 月...\n', month);
        try
            prevYear = currentYear - 1;
            nextYear = currentYear + 1;
            
            prevFileName = sprintf('%s_year_%d_month_%02d.nc', filePrefix, prevYear, month);
            nextFileName = sprintf('%s_year_%d_month_%02d.nc', filePrefix, nextYear, month);
            
            prevFilePath = fullfile(basePath, [dataType, num2str(prevYear)], prevFileName);
            nextFilePath = fullfile(basePath, [dataType, num2str(nextYear)], nextFileName);
            
            fprintf('     尝试读取文件1: %s\n', prevFilePath);
            fprintf('     尝试读取文件2: %s\n', nextFilePath);

            if ~exist(prevFilePath, 'file') || ~exist(nextFilePath, 'file')
                fprintf('     -> 失败：一个或两个文件不存在。\n');
                continue;
            end
            
            data_prev = double(ncread(prevFilePath, dataVarName));
            data_next = double(ncread(nextFilePath, dataVarName));
            
            data_prev(data_prev > 1e20) = NaN;
            data_next(data_next > 1e20) = NaN;
            
            monthly_diffs(:,:,month) = (data_prev - data_next) / 2;
            months_in_year_count = months_in_year_count + 1;
            fprintf('     -> 成功。\n');
        catch ME
             fprintf('     -> 错误！\n');
             fprintf('     -> MATLAB原始错误信息: %s\n', ME.message);
             fprintf('     -> 错误发生在文件: %s (行号: %d)\n', ME.stack(1).name, ME.stack(1).line);
        end
    end
    
    if months_in_year_count > 0
        annual_mean_rate = mean(monthly_diffs, 3, 'omitnan');
        composite_stack(:,:,i) = annual_mean_rate;
        years_processed_count = years_processed_count + 1;
        fprintf('--- 年份 %d 处理完成 (基于 %d 个月的数据)。 ---\n', currentYear, months_in_year_count);
    else
        fprintf('--- 年份 %d 处理失败，没有任何有效月份。 ---\n', currentYear);
    end
end

if years_processed_count == 0
    error('未能成功处理任何指定年份，无法生成图像。');
end

final_composite_map = mean(composite_stack, 3, 'omitnan');

if all(isnan(final_composite_map(:)))
    error('最终合成结果全部为NaN，因此无法生成图像。请检查上面日志中每个月的处理是否都失败了。');
end

fprintf('\n=============== 所有年份合成完毕！ ===============\n');

%% 4. 结果可视化 (使用 M_Map 工具箱)
figure('Name', [dataType ' Multi-Year Composite Analysis'], 'Position', [100, 100, 1200, 800]);

lon_mmap = lon;
if max(lon_mmap) > 180.5
    lon_mmap(lon_mmap > 180) = lon_mmap(lon_mmap > 180) - 360;
end
[lon_mmap_sorted, sort_idx] = sort(lon_mmap);
final_composite_map_sorted = final_composite_map(sort_idx, :);

m_proj('Robinson', 'long', 180);
ax = gca;
ax.Position = [0.05, 0.15, 0.9, 0.8];
[longrid, latgrid] = meshgrid(lon_mmap_sorted, lat);
m_pcolor(longrid, latgrid, final_composite_map_sorted');
set(findobj(gca,'Type','surface'), 'EdgeColor', 'none');
hold on;
m_coast('patch', [0.7 0.7 0.7], 'EdgeColor', 'k');
xtick_locations = -180:60:180;
ytick_locations = -90:30:90;
m_grid('tickdir','out', 'xtick', xtick_locations, 'ytick', ytick_locations, 'linestyle', 'none', 'fontsize', 12);

if cmocean_is_available
    colormap(ax, cmocean('balance'));
else
    colors = [0 0 1; 1 1 1; 1 0 0];
    positions = [0, 0.5, 1];
    my_bwr = interp1(positions, colors, linspace(0, 1, 256));
    colormap(ax, my_bwr);
end

min_val = min(final_composite_map(:), [], 'omitnan');
max_val = max(final_composite_map(:), [], 'omitnan');
max_abs_val = max(abs([min_val, max_val]));
caxis([-max_abs_val, max_abs_val]);
h_cbar = colorbar('southoutside');
cbar_pos = get(h_cbar, 'Position');
cbar_pos(2) = cbar_pos(2) - 0.04;
set(h_cbar, 'Position', cbar_pos);
num_ticks = 11;
ticks = linspace(-max_abs_val, max_abs_val, num_ticks);
tickLabels = cell(size(ticks));
for k = 1:length(ticks)
    tickLabels{k} = sprintf('%.2e', ticks(k));
end
set(h_cbar, 'Ticks', ticks, 'TickLabels', tickLabels, 'FontSize', 14);
title(h_cbar, ['合成年平均' dataType '变化率'], 'FontSize', 16);
title_str = sprintf('%s 特定年份合成变化率 (%d 个年份平均)', dataType, years_processed_count);
title(title_str, 'fontsize', 18, 'FontWeight', 'bold');

%% 5. 在命令行输出量化结果
fprintf('\n------------------ %s 多年合成分析结果 ------------------\n', dataType);
fprintf('本分析基于以下 %d 个年份的年平均变化率合成得到:\n', years_processed_count);
disp(targetYears);
fprintf('\n最终合成场的变化率范围:\n');
fprintf('  -> 最小值: %.4f\n', min_val);
fprintf('  -> 最大值: %.4f\n', max_val);
fprintf('-----------------------------------------------------------\n');