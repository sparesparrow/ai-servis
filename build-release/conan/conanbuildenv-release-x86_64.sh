script_folder="/workspace/build-release/conan"
echo "echo Restoring environment" > "$script_folder/deactivate_conanbuildenv-release-x86_64.sh"
for v in PATH LD_LIBRARY_PATH DYLD_LIBRARY_PATH
do
    is_defined="true"
    value=$(printenv $v) || is_defined="" || true
    if [ -n "$value" ] || [ -n "$is_defined" ]
    then
        echo export "$v='$value'" >> "$script_folder/deactivate_conanbuildenv-release-x86_64.sh"
    else
        echo unset $v >> "$script_folder/deactivate_conanbuildenv-release-x86_64.sh"
    fi
done


export PATH="/home/ubuntu/.conan2/p/b/flatb9a122b150c0cb/p/bin:$PATH"
export LD_LIBRARY_PATH="/home/ubuntu/.conan2/p/b/flatb9a122b150c0cb/p/lib:$LD_LIBRARY_PATH"
export DYLD_LIBRARY_PATH="/home/ubuntu/.conan2/p/b/flatb9a122b150c0cb/p/lib:$DYLD_LIBRARY_PATH"