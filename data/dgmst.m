%% 多年温度变化率的合成分析
%--------------------------------------------------------------------------
% 功能:
% 1. 【修正】手动下移Colorbar，增大与主图的间距。
% 2. 调整图形布局，避免地图与Colorbar重叠。
% 3. 确保地图坐标轴的经纬度刻度严格按照30度间隔显示。
% 4. 对指定列表中的每一年，都计算其“年平均变化率”。
% 5. 将所有指定年份的“年平均变化率”再次求平均，得到最终的合成图。
%--------------------------------------------------------------------------

%% 1. 设置
clear; clc; close all;

% --- 【用户设置区】 ---
targetYears = [1886, 1905, 1915, 1929, 1932, 1977, 1983, 2016, 2023];
% --------------------

% 检查 cmocean 工具箱是否存在
try
    cmocean('balance');
    cmocean_is_available = true;
catch
    cmocean_is_available = false;
end

% --- 基本文件设置 ---
source_file = 'gistemp1200_GHCNv4_ERSSTv5.nc';
latVarName  = 'lat';
lonVarName  = 'lon';
dataVarName = 'tempanomaly';

% --- 加载数据并进行经度转换 ---
fprintf('开始加载和预处理数据...\n');
lon_raw = ncread(source_file, lonVarName);
lat = ncread(source_file, latVarName);
time_raw = ncread(source_file, 'time');
time_origin = datenum(1800, 1, 1);
time_dates = time_origin + double(time_raw);
[Y, M, ~] = datevec(time_dates);
sst0_raw = ncread(source_file, dataVarName);
lon_shifted = lon_raw;
lon_shifted(lon_shifted < 0) = lon_shifted(lon_shifted < 0) + 360;
[lon, sort_idx] = sort(lon_shifted);
sst0 = sst0_raw(sort_idx, :, :);
fprintf('数据加载和预处理完成。\n');


%% 2. 核心计算：嵌套循环与合成
fprintf('\n=============== 开始对指定年份列表进行合成分析 ===============\n');
composite_stack = NaN(size(sst0,1), size(sst0,2), length(targetYears));
years_processed_count = 0;
for i = 1:length(targetYears)
    currentYear = targetYears(i);
    fprintf('\n--- 正在处理年份: %d ---\n', currentYear);
    monthly_diffs = NaN(size(sst0,1), size(sst0,2), 12);
    months_in_year_count = 0;
    for month = 1:12
        prev_idx = find(Y == (currentYear - 1) & M == month);
        next_idx = find(Y == (currentYear + 1) & M == month);
        if isempty(prev_idx) || isempty(next_idx)
            fprintf('  -> 跳过 %d 年 %02d 月：缺少前一年或后一年的数据。\n', currentYear, month);
            continue;
        end
        data_prev = sst0(:, :, prev_idx);
        data_next = sst0(:, :, next_idx);
        monthly_diffs(:,:,month) = (data_prev - data_next) / 2;
        months_in_year_count = months_in_year_count + 1;
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
final_composite_map = mean(composite_stack, 3, 'omitnan');
fprintf('\n=============== 所有年份合成完毕！ ===============\n');

%% 3. 结果可视化
figure('Name', 'Multi-Year Composite Analysis', 'Position', [100, 100, 1200, 800]);

% 手动创建坐标轴，预留底部空间
ax = axes('Position', [0.05, 0.15, 0.9, 0.8]);

m_proj('Robinson', 'lon', [0 360]);
[plon, plat] = meshgrid(lon, lat);
m_pcolor(plon, plat, final_composite_map');
set(findobj(gca,'Type','surface'), 'EdgeColor', 'none');
hold on;
m_coast('color', 'k', 'linewidth', 1.5);
xtick_locations = 0:30:360;
ytick_locations = -90:30:90;
m_grid('tickdir','out', 'xtick', xtick_locations, 'ytick', ytick_locations, 'linestyle', 'none', 'fontsize', 12);

if cmocean_is_available
    colormap(ax, cmocean('balance'));
else
    colormap(ax, 'parula');
end

min_val = min(final_composite_map(:));
max_val = max(final_composite_map(:));
max_abs_val = 0.4;
caxis([-max_abs_val, max_abs_val]);
h_cbar = colorbar('southoutside');

% --- 【关键改动】手动调整 Colorbar 的垂直位置 ---
cbar_pos = get(h_cbar, 'Position');      % 获取当前位置 [左, 底, 宽, 高]
cbar_pos(2) = cbar_pos(2) - 0.1;      % 将'底'的位置向下移动4%的窗口高度
set(h_cbar, 'Position', cbar_pos);     % 应用新位置
% ------------------------------------------------

num_ticks = 11;
ticks = linspace(-max_abs_val, max_abs_val, num_ticks);
tickLabels = cell(size(ticks));
for k = 1:length(ticks)
    tickLabels{k} = sprintf('%.3f', ticks(k));
end
set(h_cbar, 'Ticks', ticks, 'TickLabels', tickLabels, 'FontSize', 14);
title(h_cbar, '合成年平均温度变化率 (K/月)', 'FontSize', 16);
title_str = sprintf('GMST特定年份合成温度变化率 (%d 个年份平均)', years_processed_count);
title(title_str, 'fontsize', 18, 'FontWeight', 'bold');

%% 4. 在命令行输出量化结果
fprintf('\n------------------ 多年合成分析结果 ------------------\n');
fprintf('本分析基于以下 %d 个年份的年平均变化率合成得到:\n', years_processed_count);
disp(targetYears);
fprintf('\n最终合成场的变化率范围:\n');
fprintf('  -> 最小值: %.4f K/月\n', min_val);
fprintf('  -> 最大值: %.4f K/月\n', max_val);
fprintf('----------------------------------------------------------\n');