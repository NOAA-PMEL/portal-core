var dagcomponentfuncs = window.dashAgGridComponentFunctions = window.dashAgGridComponentFunctions || {};

// ===================================================================
// 1. EDIT DROPDOWN BUTTON (Dynamic Collision Detection)
// ===================================================================
dagcomponentfuncs.EditDropdownButton = function (props) {
    const [open, setOpen] = React.useState(false);
    const [dropUp, setDropUp] = React.useState(false); // Track direction dynamically
    const wrapperRef = React.useRef(null);

    // Dynamic position checking on open
    React.useEffect(function () {
        if (!open || !wrapperRef.current) return;

        // Find the grid body or use the window if the grid isn't a scroll container
        // AG-Grid keeps elements inside a '.ag-body-viewport'
        const gridViewport = wrapperRef.current.closest('.ag-body-viewport') || document.body;
        
        const buttonRect = wrapperRef.current.getBoundingClientRect();
        const gridRect = gridViewport.getBoundingClientRect();

        // Calculate available space below the button inside the grid
        const spaceBelow = gridRect.bottom - buttonRect.bottom;
        
        // Hardcoded estimate of your dropdown height (approx 130px for 3 items)
        const estimatedDropdownHeight = 140; 

        // If space below is less than the dropdown height, flip it up!
        if (spaceBelow < estimatedDropdownHeight) {
            setDropUp(true);
        } else {
            setDropUp(false);
        }
    }, [open]);

    // Close dropdown when clicking outside
    React.useEffect(function () {
        function handleClickOutside(e) {
            if (wrapperRef.current && !wrapperRef.current.contains(e.target)) {
                setOpen(false);
            }
        }
        document.addEventListener('mousedown', handleClickOutside);
        return function () { document.removeEventListener('mousedown', handleClickOutside); };
    }, []);

    function handleSelect(target) {
        setOpen(false);
        window.dash_clientside.set_props("edit-click-store", {
            data: { db_id: props.node.id, target: target }
        });
    }

    const menuItems = [
        { target: 'metadata',  icon: '✏️', label: 'Metadata'},
        { target: 'step-1',    icon: '📄', label: 'Data Files'},
        { target: 'step-2',    icon: '📎', label: 'Supplemental Files'},
    ];

    return React.createElement(
        'div',
        { ref: wrapperRef, style: { position: 'relative', display: 'inline-block', zIndex: open ? 1000 : 1 } },

        // Trigger button
        React.createElement(
            'button',
            {
                onClick: function () { setOpen(function (o) { return !o; }); },
                style: {
                    display: 'inline-flex', alignItems: 'center', gap: '4px',
                    background: 'rgba(255,255,255,0.04)', border: '2px solid #666',
                    borderRadius: '4px', color: '#aaa', cursor: 'pointer',
                    fontSize: '12px', fontWeight: '500', padding: '2px 6px',
                    whiteSpace: 'nowrap'
                }
            },
            'Edit ',
            React.createElement('span', { style: {
                fontSize: '9px', opacity: 0.6,
                display: 'inline-block',
                transform: open ? 'rotate(180deg)' : 'rotate(0deg)',
                transition: 'transform 0.15s'
            }}, '▾')
        ),

        // Dropdown menu
        open && React.createElement(
            'div',
            {
                style: {
                    position: 'absolute', 
                    // Dynamic Positioning based on dropUp state
                    top: dropUp ? 'auto' : 'calc(100% + 5px)', 
                    bottom: dropUp ? 'calc(100% + 5px)' : 'auto',
                    right: 0,
                    background: '#1e1e1e', 
                    border: '2px solid #00d2ff',
                    borderRadius: '6px', 
                    boxShadow: '0 8px 32px rgba(0, 210, 255, 0.25)',
                    minWidth: '210px', 
                    zIndex: 9999, 
                    overflow: 'hidden'
                }
            },

            // Menu items
            menuItems.map(function (item) {
                return React.createElement(
                    'button',
                    {
                        key: item.target,
                        onClick: function () { handleSelect(item.target); },
                        style: {
                            display: 'flex', alignItems: 'center', gap: '10px',
                            background: 'none', border: 'none', color: '#aaa',
                            cursor: 'pointer', fontSize: '12px', padding: '9px 14px',
                            textAlign: 'left', width: '100%', transition: 'background 0.1s'
                        },
                        onMouseOver: function (e) { e.currentTarget.style.background = 'rgba(56,217,169,0.08)'; e.currentTarget.style.color = '#00d2ff'; },
                        onMouseOut:  function (e) { e.currentTarget.style.background = 'none'; e.currentTarget.style.color = '#aaa'; }
                    },
                    React.createElement('span', { style: { fontSize: '13px', width: '18px', textAlign: 'center' } }, item.icon),
                    React.createElement('div', { style: { display: 'flex', flexDirection: 'column' } },
                        React.createElement('span', null, item.label),
                        React.createElement('span', { style: { fontSize: '10px', color: '#444', marginTop: '1px' } }, item.sub)
                    )
                );
            })
        )
    );
};

// ===================================================================
// 2. SUBMIT DROPDOWN BUTTON (Dynamic Collision Detection)
// ===================================================================
dagcomponentfuncs.SubmitDropdownButton = function (props) {
    const [open, setOpen] = React.useState(false);
    const [destinations, setDestinations] = React.useState([]);
    const [dropUp, setDropUp] = React.useState(false); // Track direction dynamically
    const wrapperRef = React.useRef(null);

    // Dynamic position checking on open
    React.useEffect(function () {
        if (!open || !wrapperRef.current) return;

        // Find AG-Grid's internal viewport or default to document.body
        const gridViewport = wrapperRef.current.closest('.ag-body-viewport') || document.body;
        
        const buttonRect = wrapperRef.current.getBoundingClientRect();
        const gridRect = gridViewport.getBoundingClientRect();

        // Available space below the button
        const spaceBelow = gridRect.bottom - buttonRect.bottom;
        
        // Dynamically estimate height based on how many server configurations loaded
        // ~35px height per item + 20px padding buffer
        const estimatedDropdownHeight = (destinations.length * 35) + 20; 

        // If space is tight, flip it up!
        if (spaceBelow < estimatedDropdownHeight) {
            setDropUp(true);
        } else {
            setDropUp(false);
        }
    }, [open, destinations]); // Triggers when menu opens or when destinations finish loading

    // Close dropdown when clicking outside
    React.useEffect(function () {
        function handleClickOutside(e) {
            if (wrapperRef.current && !wrapperRef.current.contains(e.target)) {
                setOpen(false);
            }
        }
        document.addEventListener('mousedown', handleClickOutside);
        return function () { document.removeEventListener('mousedown', handleClickOutside); };
    }, []);

    function handleSelect(destination) {
        setOpen(false);
        window.dash_clientside.set_props("archive-click-store", {
            data: { db_id: props.node.id, destination: destination }
        });
    }

    // Fetch destinations from server config on mount
    React.useEffect(function () {
        fetch('archives-config')
            .then(function (r) { return r.json(); })
            .then(function (data) { setDestinations(data); })
            .catch(function (err) { console.error('Failed to load archive config:', err); });
    }, []);

    return React.createElement(
        'div',
        { ref: wrapperRef, style: { position: 'relative', display: 'inline-block', zIndex: open ? 1000 : 1 } },

        React.createElement(
            'button',
            {
                onClick: function () { setOpen(function (o) { return !o; }); },
                style: {
                    display: 'inline-flex', alignItems: 'center', gap: '4px',
                    background: 'rgba(56,217,169,0.05)', border: '2px solid rgba(56,217,169,0.6)',
                    borderRadius: '4px', color: '#38d9a9', cursor: 'pointer',
                    fontSize: '12px', fontWeight: '500', padding: '2px 6px',
                    whiteSpace: 'nowrap'
                }
            },
            'Submit ',
            React.createElement('span', { style: {
                fontSize: '9px', opacity: 0.6,
                display: 'inline-block',
                transform: open ? 'rotate(180deg)' : 'rotate(0deg)',
                transition: 'transform 0.15s'
            }}, '▾')
        ),

        open && React.createElement(
            'div',
            {
                style: {
                    position: 'absolute', 
                    // Dynamic Positioning based on dropUp state
                    top: dropUp ? 'auto' : 'calc(100% + 5px)', 
                    bottom: dropUp ? 'calc(100% + 5px)' : 'auto',
                    right: 0,
                    background: '#1e1e1e', 
                    border: '2px solid #00d2ff',
                    borderRadius: '6px', 
                    boxShadow: '0 8px 32px rgba(0, 210, 255, 0.25)',
                    minWidth: '240px', 
                    zIndex: 9999, 
                    overflow: 'hidden'
                }
            },

            destinations.map(function (dest) {
                return React.createElement(
                    'button',
                    {
                        key: dest.key,
                        onClick: dest.enabled ? function () { handleSelect(dest.key); } : null,
                        style: {
                            display: 'flex', alignItems: 'center', gap: '10px',
                            background: 'none', border: 'none',
                            color: dest.enabled ? '#aaa' : '#777',
                            cursor: dest.enabled ? 'pointer' : 'default',
                            fontSize: '12px', padding: '9px 14px',
                            textAlign: 'left', width: '100%',
                            opacity: dest.enabled ? 1 : 0.5
                        },
                        onMouseOver: dest.enabled ? function (e) { e.currentTarget.style.background = 'rgba(56,217,169,0.08)'; e.currentTarget.style.color = '#00d2ff'; } : null,
                        onMouseOut:  dest.enabled ? function (e) { e.currentTarget.style.background = 'none'; e.currentTarget.style.color = '#aaa'; } : null,
                    },
                    React.createElement('span', { style: { fontSize: '13px', width: '18px', textAlign: 'center' } }, dest.icon),
                    React.createElement('div', { style: { display: 'flex', flexDirection: 'column' } },
                        React.createElement('span', null, dest.label),
                        React.createElement('span', { style: { fontSize: '10px', color: '#444', marginTop: '1px' } }, dest.sub)
                    )
                );
            })
        )
    );
};

// ===================================================================
// 3. DATA FILE LIST RENDERER
// ===================================================================
dagcomponentfuncs.DataFileListRenderer = function (props) {
    if (!props.value || props.value.length === 0) {
        return React.createElement('span', {style: {color: '#aaa', fontStyle: 'italic', fontSize: '0.9em'}}, 'No data files');
    }

    var fileItems = props.value.map(function(filename) {
        function onFileClick(e) {
            e.stopPropagation();
            window.dash_clientside.set_props("file-click-store", {
                data: { filename: filename, db_id: props.node.id, colId: props.column.colId }
            });
        }

        return React.createElement('div', {
            onClick: onFileClick,
            style: {
                backgroundColor: '#e3f2fd', border: '1px solid #90caf9', borderRadius: '4px',
                padding: '2px 8px', // Tightened vertical padding from 6px to 2px to make it shorter
                marginBottom: '4px', cursor: 'pointer', 
                width: '95%', // Restored your original horizontal width layout
                fontSize: '0.9em', fontWeight: '500', color: '#0d47a1',
                display: 'flex', alignItems: 'center', overflow: 'hidden', minWidth: 0,
                boxSizing: 'border-box'
            },
            title: filename,
            onMouseOver: function(e){ e.currentTarget.style.backgroundColor = '#bbdefb'; },
            onMouseOut:  function(e){ e.currentTarget.style.backgroundColor = '#e3f2fd'; }
        },
            React.createElement('div', {style: { 
                display: 'flex', flexDirection: 'column',
                overflow: 'hidden', minWidth: 0, width: '100%'
            }},
                // 1. Filename row
                React.createElement('span', {style: {
                    overflow: 'hidden',
                    textOverflow: 'ellipsis',
                    whiteSpace: 'nowrap',
                    minWidth: 0,
                    lineHeight: '1.2'
                }}, filename),
                
                // 2. Sub-row: Chart icon directly adjacent to preview text to save vertical space
                React.createElement('div', {style: { 
                    display: 'flex', 
                    alignItems: 'center', 
                    marginTop: '1px',
                    lineHeight: '1'
                }},
                    React.createElement('span', {style: {fontSize: '1em', marginRight: '4px'}}, '📈'),
                    React.createElement('span', {style: {
                        fontSize: '0.8em',
                        color: '#1565c0',
                        opacity: 0.75,
                        fontWeight: '400',
                    }}, 'Click to preview ➔')
                )
            )
        );
    });

    return React.createElement('div', { style: { padding: '4px 0' } }, fileItems);
};

// ===================================================================
// 4. SUPPLEMENTAL FILE LIST RENDERER
// ===================================================================
dagcomponentfuncs.SuppFileListRenderer = function (props) {
    if (!props.value || props.value.length === 0) {
        return React.createElement('span', {style: {color: '#aaa', fontStyle: 'italic', fontSize: '0.9em'}}, 'No supplemental files');
    }
    var fileItems = props.value.map(function(filename) {
        function onFileClick(e) {
            e.stopPropagation();
            window.dash_clientside.set_props("file-click-store", {
                data: { filename: filename, db_id: props.node.id, colId: props.column.colId }
            });
        }
        return React.createElement('div', {
            onClick: onFileClick,
            style: {
                backgroundColor: '#fff3e0', border: '1px solid #ffb74d', borderRadius: '4px',
                padding: '2px 8px', marginBottom: '4px', cursor: 'pointer', width: '95%',
                
                // Forces the box to match the vertical thickness of the data file boxes
                minHeight: '36px', 
                // Ensures the icon and filename stay centered vertically inside that thickness
                display: 'flex', alignItems: 'center', 
                
                fontSize: '0.9em', color: '#e65100', 
                overflow: 'hidden', minWidth: 0,
                boxSizing: 'border-box'
            },
            title: filename,
            onMouseOver: function(e){ e.currentTarget.style.backgroundColor = '#ffe0b2'; },
            onMouseOut:  function(e){ e.currentTarget.style.backgroundColor = '#fff3e0'; }
        },
            React.createElement('span', {style: {
                marginRight: '6px', 
                fontSize: '1em', 
                lineHeight: '1'
            }}, '📄'),
            React.createElement('span', {style: {
                overflow: 'hidden',
                textOverflow: 'ellipsis',
                whiteSpace: 'nowrap',
                minWidth: 0,
                lineHeight: '1.2' 
            }}, filename)
        );
    });
    return React.createElement('div', { style: { padding: '4px 0' } }, fileItems); 
};

// ===================================================================
// 3. New Badge Renderer when new submissions get added
// ===================================================================
// ===================================================================
// 3. New Badge Renderer when new submissions get added
// ===================================================================
dagcomponentfuncs.SubmissionIdRenderer = function (props) {
    // Look directly at the row data flag
    var isNew = props.data && props.data.is_new;

    return React.createElement(
        'span',
        { style: { display: 'inline-flex', alignItems: 'center', gap: '6px' } },
        React.createElement('span', null, props.value),
        isNew && React.createElement(
            'span',
            {
                style: {
                    display: 'inline-block',
                    background: 'rgba(0,210,255,0.12)',
                    border: '1px solid rgba(0,210,255,0.45)',
                    color: '#00d2ff',
                    fontSize: '10px',
                    fontWeight: '600',
                    padding: '1px 7px',
                    borderRadius: '10px',
                    letterSpacing: '0.04em',
                    lineHeight: '1.6'
                }
            },
            'NEW'
        )
    );
};
