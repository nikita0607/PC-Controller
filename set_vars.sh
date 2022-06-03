if cd ./env/bin ; then
    . ./activate

    old_API_HOST=$API_HOST
    old_API_PORT=$API_PORT
    old_DATABASE_HOST=$DATABASE_HOST
    old_DATABASE_PORT=$DATABASE_PORT

    rm activate
    cp old_activate activate

    echo Enter API_HOST ; read l_API_HOST
    echo Enter API_PORT ; read l_API_PORT
    echo Enter DATABASE_HOST ; read l_DATABASE_HOST
    echo Enter DATABASE_PORT ; read l_DATABASE_PORT

    if [ "$l_API_HOST" = "" ] ; then
        l_API_HOST=$old_API_HOST
    elif [ "$l_API_HOST" = "def" ] ; then
        l_API_HOST="127.0.0.1"
    fi
    
    if [ "$l_API_PORT" = "" ] ; then
        l_API_PORT=$old_API_PORT
    elif [ "$l_API_PORT" = "def" ] ; then
        l_API_PORT="8000"
    fi

    if [ "$l_DATABASE_HOST" = "" ] ; then
        l_DATABASE_HOST=$old_DATABASE_HOST
    elif [ "$l_DATABASE_HOST" = "def" ] ; then
        l_DATABASE_HOST="127.0.0.1"
    fi
    
    if [ "$l_DATABASE_PORT" = "" ] ; then
        l_DATABASE_PORT=$old_DATABASE_PORT
    elif [ "$l_DATABASE_PORT" = "def" ] ; then
        l_DATABASE_PORT="8001"
    fi

    echo "export API_HOST=$l_API_HOST" >> activate
    echo "export API_PORT=$l_API_PORT" >> activate
    
    echo "export DATABASE_HOST=$l_DATABASE_HOST" >> activate
    echo "export DATABASE_PORT=$l_DATABASE_PORT" >> activate
fi
