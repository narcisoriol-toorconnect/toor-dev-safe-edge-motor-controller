-- Import json module
local json = require("json")

-- Get the current node
local current_node_json, err = get_current_node()
if not current_node_json then
    return nil, "Failed to get current node: " .. tostring(err)
end

-- Decode the current node JSON
local current_node, decode_err = json.decode(current_node_json)
if not current_node then
    return nil, ("Failed to decode current node JSON: " .. tostring(decode_err))
end

-- Get sw_requirements_group node
local sw_requirements_group_id = current_node["parent"]
if not sw_requirements_group_id then
    return nil, "Current node does not have a parent sw_requirements_group"
end
local sw_requirements_group_json, err = get_node("sw_requirements_group", sw_requirements_group_id)
if not sw_requirements_group_json then
    return nil, "Failed to get sw_requirements_group node: " .. tostring(err)
end

-- Decode sw_requirements_group node JSON
local sw_requirements_group, decode_err = json.decode(sw_requirements_group_json)
if not sw_requirements_group then
    return nil, "Failed to decode sw_requirements_group JSON: " .. tostring(decode_err)
end

-- Get requirements_count from sw_requirements_group node (default 0)
local requirements_count = sw_requirements_group["fields"]["requirements_count"] or 0

-- Get label from sw_requirements_group node
local sw_requirements_group_label = sw_requirements_group["label"]

-- Create new label: SR-<sw_requirements_group>-<n>
local new_label = "SR-" .. sw_requirements_group_label .. "-" .. (requirements_count + 1)

-- Update sw_requirements_group node's requirements_count by incrementing it by 1
local ok, err = update_node("sw_requirements_group", sw_requirements_group_id, "requirements_count=" .. (requirements_count + 1))
if not ok then
    return nil, "Failed to update requirements_count: " .. tostring(err)
end

-- Set the new label for the current node
local ok, label_err = update_current_node_label(new_label)
if not ok then
    return nil, "Failed to update current node label: " .. tostring(label_err)
end
