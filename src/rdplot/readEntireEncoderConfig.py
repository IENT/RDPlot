import re


def main():
    all_configs = []
    config1 = open('RaceHorses_416x240_QP18_GeoLambdaModifier3.1_enc.log','r')
    config2 = open('RaceHorses_416x240_QP18_GeoLambdaModifier4.1_enc.log','r')
    config3 = open('RaceHorses_416x240_QP22_GeoLambdaModifier4.6_enc.log','r')

    all_configs.append(parseEncoderConfig(config1))
    all_configs.append(parseEncoderConfig(config2))
    all_configs.append(parseEncoderConfig(config3))

    diff_dict = {}
    value_filter = ['.yuv','.bin','.hevc','.jem']
    key_filter = []
    for i in range(len(all_configs) - 1):
        current_item, next_item = all_configs[i], all_configs[i + 1]
        diff = set(current_item.values()) ^ set(next_item.values())
        for (key, value) in set(current_item.items()) ^ set(next_item.items()):
            if all(y not in key for y in key_filter):
                if all(x not in value for x in value_filter):
                    if key not in diff_dict:
                        diff_dict[key] = []
                        diff_dict[key].append(value)
                    else:
                        if value not in diff_dict[key]:
                            diff_dict[key].append(value)
                
    print(diff_dict)

def parseEncoderConfig(textfile): 
    all = textfile.read()
    lines = all.split('\n')
    cleanlist = []
    for one_line in lines:
        if one_line:
            if 'Non-environment-variable-controlled' in one_line:
                break
            if one_line.count(':')==1:
                clean_line = one_line.strip(' \n\t\r')
                clean_line = clean_line.replace(' ','')
                cleanlist.append(clean_line)
            #elif one_line.count(':')>1:
            # Ignore Multiline stuff for now
            # TODO: do something smart
            #else:
            # Something else happened, do nothing
            # TODO: do something smart
    parsed_config = dict(item.split(':') for item in cleanlist)
    return parsed_config

if __name__ == '__main__':
    main()