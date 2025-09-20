function map()
%% MATLAB NC文件浏览器 (V7 - 添加搜索跳转功能)
%--------------------------------------------------------------------------
% 功能:
% 1. 【新增】添加一个输入框和“跳转”按钮，可根据输入的“年份月份”快速定位。
% 2. 手动创建并使用蓝-白-红(bwr)发散型色谱。
% 3. 自动计算并固定全局颜色轴。
% 4. 已修正数据转置和地图经度范围问题。
% 5. 使用稳健的嵌套函数结构，无回调bug。
%--------------------------------------------------------------------------

%% 1. 设置和数据预读取
folderPath  = 'D:\SCIENCE\atmospheric_physic\daqi\qixiangzhishu\gmst\data\sea_level_grid';
latVarName  = 'latitude';
lonVarName  = 'longitude';
dataVarName = 'sla';

filePattern = fullfile(folderPath, '*.nc');
ncFiles = dir(filePattern);
if isempty(ncFiles)
    error('在指定的文件夹中没有找到任何 .nc 文件: %s', folderPath);
end

disp('开始预读取所有NC文件...');
allData = struct('title', {}, 'date_str', {}, 'lat', {}, 'lon', {}, 'data', {});
for i = 1:length(ncFiles)
    baseFileName = ncFiles(i).name;
    fullFilePath = fullfile(folderPath, baseFileName);
    fprintf('正在读取: %s\n', baseFileName);
    
    try % 提取标题和用于搜索的日期字符串
        nameParts = split(baseFileName, '_');
        yearMonthStr = nameParts{5};
        allData(i).title = sprintf('SLA for %s-%s', yearMonthStr(1:4), yearMonthStr(5:6));
        allData(i).date_str = yearMonthStr; % 保存 "199810" 格式的字符串用于搜索
    catch
        allData(i).title = strrep(baseFileName, '_', ' ');
        allData(i).date_str = ''; % 如果格式不匹配则为空
    end
    
    allData(i).lat = double(ncread(fullFilePath, latVarName));
    allData(i).lon = double(ncread(fullFilePath, lonVarName));
    temp_data = double(ncread(fullFilePath, dataVarName, [1 1 1], [inf inf 1]));
    allData(i).data = temp_data';
end
disp('所有文件读取完毕。');

%% 2. 计算全局颜色范围
globalMin = inf;
globalMax = -inf;
for i = 1:length(allData)
    minVal = min(allData(i).data(:), [], 'omitnan');
    maxVal = max(allData(i).data(:), [], 'omitnan');
    if minVal < globalMin, globalMin = minVal; end
    if maxVal > globalMax, globalMax = maxVal; end
end
fprintf('所有数据的全局范围: Min = %.4f, Max = %.4f\n', globalMin, globalMax);

%% 3. 创建自定义的蓝-白-红(bwr)颜色图
colors = [0, 0, 1; 1, 1, 1; 1, 0, 0];
positions = [0, 0.5, 1];
x = linspace(0, 1, 256);
my_bwr = interp1(positions, colors, x);

%% 4. 创建GUI窗口和主图
if isempty(allData)
    error('未能从任何文件中读取到有效数据。');
end

fig = figure('Name', 'NC文件浏览器-支持搜索', 'NumberTitle', 'off', 'Position', [100, 100, 1200, 800]);

ax = axes('Parent', fig, 'Position', [0.05, 0.15, 0.9, 0.8]);
axesm('MapProjection', 'miller', 'Frame', 'on', 'Grid', 'on', ...
      'MeridianLabel', 'on', 'ParallelLabel', 'on', 'MapLonLimit', [0 360]);
setm(ax, 'MLabelParallel', 'south');

geoshow('landareas.shp', 'FaceColor', [0.7 0.7 0.7], 'EdgeColor', 'k');
hold(ax, 'on');

h_plot = pcolorm(allData(1).lat, allData(1).lon, allData(1).data);
hold(ax, 'off');

h_cbar = colorbar(ax);
ylabel(h_cbar, 'Sea Level Anomaly (m)');
title(ax, allData(1).title, 'FontSize', 14);

caxis(ax, [globalMin, globalMax]);
colormap(ax, my_bwr);

%% 5. 创建UI交互控件
% 滑动条
h_slider = uicontrol('Parent', fig, 'Style', 'slider', 'Position', [200, 40, 600, 20], ...
    'Min', 1, 'Max', length(allData), 'Value', 1, ...
    'SliderStep', [1/(length(allData)-1) , 1/(length(allData)-1)], ...
    'Callback', @slider_callback);

% 静态文本标签
h_text = uicontrol('Parent', fig, 'Style', 'text', 'String', allData(1).title, ...
    'Position', [450, 10, 200, 20], 'FontSize', 12);

% 【新增】搜索输入框
h_edit = uicontrol('Parent', fig, 'Style', 'edit', 'Position', [820, 40, 100, 25], ...
    'String', '例如:199810', 'FontSize', 10);

% 【新增】“跳转”按钮
h_button = uicontrol('Parent', fig, 'Style', 'pushbutton', 'String', '跳转', ...
    'Position', [930, 40, 60, 25], 'FontSize', 10, ...
    'Callback', @jump_to_date_callback);

%% 6. 定义所有回调函数 (作为嵌套函数)
    
    % --- 滑动条的回调函数 ---
    function slider_callback(source, ~)
        idx = round(source.Value);
        update_plot(idx); % 调用统一的绘图更新函数
    end

    % --- 【新增】“跳转”按钮的回调函数 ---
    function jump_to_date_callback(~, ~)
        % 获取输入框中的文本
        target_str = get(h_edit, 'String');
        
        % 查找与输入文本匹配的日期
        found_idx = find(strcmp({allData.date_str}, target_str));
        
        if ~isempty(found_idx)
            % 如果找到，则更新图像和滑动条
            update_plot(found_idx(1)); % 使用找到的第一个索引
        else
            % 如果没找到，则显示一个警告对话框
            warndlg(['未找到日期: ' target_str], '搜索结果');
        end
    end

    % --- 【新增】统一的绘图更新函数，避免代码重复 ---
    function update_plot(idx)
        % 更新主图的数据
        set(h_plot, 'CData', allData(idx).data);
        
        % 更新标题和文本标签
        newTitle = allData(idx).title;
        title(ax, newTitle, 'FontSize', 14);
        set(h_text, 'String', newTitle);
        
        % 同步更新滑动条的位置
        set(h_slider, 'Value', idx);
    end

end % 主函数结束