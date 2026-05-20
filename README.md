
# run

`uv run streamlit run app.py --server.port 8501 --server.address 0.0.0.0 --client.toolbarMode hidden`


## Add to systemctl

1) `ln -s $(pwd)/web-panel.service ~/.config/systemd/user/`
2) `systemctl --user daemon-reload`
3) `systemctl --user restart web-panel.service`
